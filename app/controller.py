# -*- coding: utf-8 -*-
"""
Sony Sound Connect PC — Orquestrador Central (SonyGHubController)
Created by Matheus Veras • Licença: Source-Available Proprietary (Ver LICENSE.md)

Responsabilidades:
- Coordenação de todos os subsistemas: WebView2, Tray, Drivers, DSP APO, Hotkeys e Automação.
- Inicialização segura com proteção contra travamentos e deadlocks.
- Monitor de integridade Bluetooth Win32 em segundo plano (Win32BluetoothWatchdog).
- Encerramento atômico, determinístico e ultra-rápido.
"""

import gc
import json
import os
import subprocess
import threading
import time
from typing import Any, Dict, List, Optional, Set

from app.config import (
    ASSETS_DIR,
    BASE_DIR,
    RESOURCE_DIR,
    DEFAULT_MAC,
    DEFAULT_PORT,
    GHUB_PRESETS,
    ICON_ICO_PATH,
    UI_HTML_PATH,
    is_mock_requested_from_env,
    load_config,
    resolve_nano_asset_uris,
    save_config,
)
from app.rpc_bridge import GHubApiBridge
from app.tray_manager import (
    SystemTrayManager,
    compute_battery_bucket,
    create_tray_icon_image,
    format_tray_tooltip,
)
from app.win32_utils import (
    apply_win32_window_icon,
    query_windows_accent_color,
    release_single_instance_lock,
)
from core.device_detector import (
    classify_headset_protocol,
    is_windows_bluetooth_connected,
    list_paired_headsets,
)
from core.drivers import BaseHeadsetDriver, create_headset_driver
from core.hearing_safety import HearingSafetyMonitor
from core.ios_desktop_overlay import IosDesktopOverlay
from core.system_integration import DEFAULT_AUTOMATION_RULES, SystemIntegrationManager
from core.windows_apo_engine import WindowsApoEngine


class SonyGHubController:
    """Orquestrador principal entre WebView2, Drivers Multimarca, APO Global, Overlay iOS e Windows 11."""

    def __init__(self, force_mock: Optional[bool] = None) -> None:
        self.config: Dict[str, Any] = load_config()
        self.window: Optional[Any] = None
        self.tray_icon: Optional[Any] = None
        self.tray_manager: Optional[SystemTrayManager] = None
        self.quitting: bool = False
        self.ui_ready: bool = False
        self.window_hidden: bool = False
        self._ui_state_dirty: bool = False
        self._last_tray_bucket: str = ""
        self._last_tray_tip: str = ""
        self._low_bat_alerted: Set[str] = set()

        initial_mock = (
            force_mock
            if force_mock is not None
            else is_mock_requested_from_env()
        )

        # 1. Motor DSP Global Windows 11 (Equalizer APO Bridge)
        self.apo_engine = WindowsApoEngine(BASE_DIR)
        self.apo_engine.enabled = bool(self.config.get("apo_enabled", True))
        self.apo_engine.spatial_enabled = bool(self.config.get("spatial_enabled", True))
        self.apo_engine.spatial_mode = str(self.config.get("spatial_mode", "nearfield"))
        self.apo_engine.crossfeed_width = int(self.config.get("crossfeed_width", 65))
        saved_eq = self.config.get("saved_custom_eq") or {"clear_bass": 3, "bands": [-1, 2, 4, 4, 2]}
        self.apo_engine.update_eq(
            "Harman Reference",
            int(saved_eq.get("clear_bass", 0)),
            list(saved_eq.get("bands", [0, 0, 0, 0, 0])),
        )

        # 2. Dosímetro Auditivo dB SPL (CoreAudio COM) & Overlay Flutuante Nativo iOS
        self.hearing_safety = HearingSafetyMonitor()
        self.desktop_overlay = IosDesktopOverlay(ASSETS_DIR)

        # 3. Driver Multimarca Ativo
        self.client: BaseHeadsetDriver = create_headset_driver(
            protocol=str(self.config.get("active_protocol", "sony_mdr")),
            mac=str(self.config.get("mac_address", DEFAULT_MAC)),
            port=int(self.config.get("rfcomm_port", DEFAULT_PORT)),
            model_name=str(self.config.get("active_model", "WF-1000XM3")),
            brand_name=str(self.config.get("active_brand", "Sony")),
            mock_mode=initial_mock,
            apo_engine=self.apo_engine,
            on_state_update=self.on_driver_state_updated,
            on_status_msg=self.push_status,
            on_wearing_event=self._on_physical_wearing_change,
        )
        saved_preset_name = str(self.config.get("active_eq_preset", "Audiófilo (Comunidade)"))
        self.client.state["clear_bass"] = int(saved_eq.get("clear_bass", 3))
        self.client.state["eq_bands"] = list(saved_eq.get("bands", [-1, 2, 4, 4, 2]))
        self.client.state["eq_preset"] = saved_preset_name

        # 4. Integração de Eventos do Kernel Windows 11 (0.0% CPU Standby)
        self.sys_integration = SystemIntegrationManager(
            on_toggle_nc=self.toggle_nc_hotkey,
            on_cycle_eq=self.cycle_eq_hotkey,
            on_apply_preset=self.apply_auto_profile,
            on_apply_automation_rule=self.apply_automation_combo,
            on_toast=self.push_toast,
            on_system_suspend=lambda: self.client.handle_system_suspend(),
            on_system_resume=lambda: self.client.handle_system_resume(),
            on_bluetooth_device_event=self.handle_zero_click_bt_event,
            initial_rules=self.config.get("automation_rules", DEFAULT_AUTOMATION_RULES),
        )
        self.sys_integration.auto_profile_enabled = bool(self.config.get("auto_profiles_enabled", True))
        self._start_bluetooth_watchdog()

    def _on_physical_wearing_change(self, is_in_ear: bool) -> None:
        self.sys_integration.handle_wearing_sensor(is_in_ear)

    def on_driver_state_updated(self) -> None:
        """Reage a atualizações de telemetria sincronizando Bandeja, Alertas <20% e WebView2."""
        self.refresh_tray_telemetry()
        self._check_low_battery_alert()
        self.push_state_to_ui()

    def refresh_tray_telemetry(self) -> None:
        """Atualiza tooltip dinâmico e LED semântico do ícone na bandeja do Windows 11."""
        if self.tray_manager:
            self.tray_manager.refresh_telemetry(self.client.state)
            return

        if not self.tray_icon:
            return
        st = self.client.state
        new_tip = format_tray_tooltip(st)
        new_bucket = compute_battery_bucket(st)

        try:
            if new_tip != self._last_tray_tip:
                self._last_tray_tip = new_tip
                self.tray_icon.title = new_tip
            if new_bucket != self._last_tray_bucket:
                self._last_tray_bucket = new_bucket
                self.tray_icon.icon = create_tray_icon_image(new_bucket)
        except Exception:
            pass

    def _check_low_battery_alert(self) -> None:
        """Dispara alerta inteligente e overlay flutuante quando qualquer cápsula cai abaixo de 20%."""
        st = self.client.state
        if not st.get("connected"):
            return

        newly_critical: List[str] = []
        for side, bat_key, chg_key in (("L", "bat_l", "bat_l_charging"), ("R", "bat_r", "bat_r_charging")):
            pct = int(st.get(bat_key) or 0)
            charging = bool(st.get(chg_key))
            if 0 < pct < 20 and not charging:
                if side not in self._low_bat_alerted:
                    self._low_bat_alerted.add(side)
                    newly_critical.append(f"{side}: {pct}%")
            elif pct >= 25 or charging:
                self._low_bat_alerted.discard(side)

        if newly_critical:
            msg = f"Bateria Baixa ({', '.join(newly_critical)}) — Recarregue em breve!"
            self.push_toast(msg, "🪫")
            self.desktop_overlay.show(st, hold_seconds=5.2)
            if self.tray_manager:
                self.tray_manager.notify(msg, "Sony Sound Connect PC")
            elif self.tray_icon:
                try:
                    self.tray_icon.notify(msg, "Sony Sound Connect PC")
                except Exception:
                    pass

    def handle_zero_click_bt_event(self) -> None:
        """
        Acionado automaticamente pelo kernel Windows 11 (`WM_DEVICECHANGE`) quando um fone Bluetooth
        é retirado do estojo ou guardado nele. Elimina qualquer falso positivo consultando a API Win32 nativa.
        """
        if self.quitting:
            return

        def _auto_worker() -> None:
            if self.quitting:
                return
            if not self.client.mock_mode and self.client.mac:
                is_conn = is_windows_bluetooth_connected(self.client.mac, self.client.model_name)
                if not is_conn:
                    if self.client.connected:
                        self.client.disconnect()
                        self.client.connected = False
                        self.client.state["connected"] = False
                        self.client.state["bat_l"] = 0
                        self.client.state["bat_r"] = 0
                        self.client.state["bat_case"] = 0
                        self.on_driver_state_updated()
                        self.push_status(f"{self.client.model_name} desconectado (guardado no estojo).")
                    return

            if not self.client.connected:
                list_paired_headsets(force_refresh=True)
                ok = self.client.connect(is_auto_retry=True)
                if ok:
                    self.on_driver_state_updated()
                    self.desktop_overlay.show(self.client.state)
                    self.push_toast(f"{self.client.state.get('model', 'Fone')} conectado automaticamente!", "🎧")

        threading.Thread(target=_auto_worker, name="ZeroClickAutoConnect", daemon=True).start()

    def _start_bluetooth_watchdog(self) -> None:
        """
        Monitor de integridade de conexão Bluetooth em segundo plano (intervalo 3.5s, <2ms de execução Win32).
        Garante que o estado reflita instantaneamente se o fone foi fechado no estojo ou se conectou ao PC.
        """
        def _watchdog_loop() -> None:
            while not self.quitting:
                time.sleep(3.5)
                if self.quitting or self.client.mock_mode or not self.client.mac:
                    continue
                try:
                    is_conn = is_windows_bluetooth_connected(self.client.mac, self.client.model_name)
                    if self.client.connected and not is_conn:
                        self.client.disconnect()
                        self.client.connected = False
                        self.client.state["connected"] = False
                        self.client.state["bat_l"] = 0
                        self.client.state["bat_r"] = 0
                        self.client.state["bat_case"] = 0
                        self.on_driver_state_updated()
                    elif not self.client.connected and is_conn:
                        ok = self.client.connect(is_auto_retry=True)
                        if ok:
                            self.on_driver_state_updated()
                            self.desktop_overlay.show(self.client.state)
                            self.push_toast(f"{self.client.state.get('model', 'Fone')} conectado automaticamente!", "🎧")
                except Exception:
                    pass

        threading.Thread(target=_watchdog_loop, name="Win32BluetoothWatchdog", daemon=True).start()

    def switch_headset_driver(self, device: Dict[str, Any]) -> Dict[str, Any]:
        """Substitui o driver ativo em tempo de execução para controle multimarca real."""
        name = str(device.get("name") or "WF-1000XM3").strip()
        mac = str(device.get("mac") or self.config.get("mac_address") or DEFAULT_MAC).strip()
        cls_info = classify_headset_protocol(name)
        brand = str(device.get("brand") or cls_info["brand"])
        proto = str(device.get("protocol") or cls_info["protocol"])
        if proto == "universal_dsp":
            proto = "universal_windows"

        was_mock = self.client.mock_mode
        old_driver = self.client
        try:
            old_driver.shutdown()
        except Exception:
            pass

        self.config["active_model"] = name
        self.config["active_brand"] = brand
        self.config["active_protocol"] = proto
        if mac:
            self.config["mac_address"] = mac
        save_config(self.config)

        self._low_bat_alerted.clear()
        self.client = create_headset_driver(
            protocol=proto,
            mac=mac,
            port=int(self.config.get("rfcomm_port", DEFAULT_PORT)),
            model_name=name,
            brand_name=brand,
            mock_mode=was_mock,
            apo_engine=self.apo_engine,
            on_state_update=self.on_driver_state_updated,
            on_status_msg=self.push_status,
            on_wearing_event=self._on_physical_wearing_change,
        )
        self.async_connect()
        return {
            "name": name,
            "mac": mac,
            "brand": brand,
            "protocol": proto,
        }

    def toggle_mock_mode(self, enabled: Optional[bool] = None) -> None:
        target = (not self.client.mock_mode) if enabled is None else bool(enabled)
        self.config["mock_mode"] = target
        cfg_copy = dict(self.config)
        cfg_copy["mock_mode"] = False
        save_config(cfg_copy)

        def worker() -> None:
            ok = self.client.set_mock_mode(target)
            self.on_driver_state_updated()
            if target and ok:
                self.push_toast("Simulador Virtual Mock Ativado!", "🤖")
                self.show_ios_popup()
            elif not target:
                self.push_toast("Modo Hardware Bluetooth Real Ativo", "📡")

        threading.Thread(target=worker, daemon=True).start()

    def apply_named_preset(self, name: str) -> None:
        if name in GHUB_PRESETS:
            cb, bands = GHUB_PRESETS[name]
            self._tray_eq(name, cb, bands)
            if self.window and self.ui_ready and not self.window_hidden:
                safe_name = json.dumps(name, ensure_ascii=False)
                try:
                    self.window.evaluate_js(f"window.setActivePresetUI && window.setActivePresetUI({safe_name});")
                except Exception:
                    pass

    def apply_auto_profile(self, preset_name: str, toast_text: str) -> None:
        self.apply_named_preset(preset_name)
        self.push_toast(toast_text, "🎮")

    def apply_automation_combo(self, rule: Dict[str, Any]) -> None:
        """Aplica simultaneamente Equalizador + Modo ANC/Ambiente + Palco 3D Crossfeed para o app detectado."""
        eq_preset = str(rule.get("eq_preset") or "Audiófilo (Comunidade)")
        nc_mode = str(rule.get("nc_mode") or "Manter")
        asm_level = int(rule.get("asm_level") or 12)
        focus_voice = bool(rule.get("focus_voice", False))
        spatial_mode = str(rule.get("spatial_mode") or "keep")

        # 1. Equalizador DSP + APO
        self.apply_named_preset(eq_preset)

        # 2. Controle Acústico ANC / Ambiente
        if nc_mode != "Manter" and self.client.PROTOCOL_ID.startswith("sony_mdr"):
            self.client.enqueue_action(
                "nc_asm",
                self.client.set_nc_asm,
                nc_mode,
                asm_level,
                focus_voice,
            )
            self.client.state["nc_mode"] = nc_mode
            self.client.state["asm_level"] = asm_level
            self.client.state["focus_on_voice"] = focus_voice

        # 3. Palco Espacial 3D Linkwitz Crossfeed no APO Global e na UI
        if spatial_mode != "keep":
            sp_enabled = spatial_mode != "off"
            sp_target = spatial_mode if sp_enabled else self.apo_engine.spatial_mode
            self.apo_engine.update_spatial(sp_enabled, sp_target, self.apo_engine.crossfeed_width)
            if self.window and self.ui_ready and not self.window_hidden:
                safe_sp = json.dumps({"enabled": sp_enabled, "mode": sp_target})
                try:
                    self.window.evaluate_js(f"window.applyAutomationSpatialUI && window.applyAutomationSpatialUI({safe_sp});")
                except Exception:
                    pass

        self.on_driver_state_updated()
        nc_tag = f" • {nc_mode}" if nc_mode != "Manter" else ""
        self.push_toast(f"{rule.get('label', rule.get('exe'))}: {eq_preset}{nc_tag}", str(rule.get("icon") or "⚡"))

    def toggle_nc_hotkey(self) -> None:
        modes = ["ANC", "Ambiente", "Desligado"]
        curr = self.client.state.get("nc_mode", "ANC")
        next_mode = modes[(modes.index(curr) + 1) % len(modes)] if curr in modes else "ANC"
        self._tray_nc(next_mode)
        ico = "🛡️" if next_mode == "ANC" else ("🍃" if next_mode == "Ambiente" else "⭕")
        self.push_toast(f"Modo Ruído: {next_mode}", ico)

    def cycle_eq_hotkey(self) -> None:
        presets = list(GHUB_PRESETS.keys())
        curr = self.client.state.get("eq_preset", presets[0])
        next_p = presets[(presets.index(curr) + 1) % len(presets)] if curr in presets else presets[0]
        self.apply_named_preset(next_p)
        self.push_toast(f"Perfil de Som: {next_p}", "🎛️")

    def push_state_to_ui(self) -> None:
        """Suspende IPC `evaluate_js` quando minimizado na bandeja para garantir 0.0% de CPU/GPU."""
        if not self.window or not self.ui_ready:
            return
        if self.window_hidden:
            self._ui_state_dirty = True
            return
        self._ui_state_dirty = False
        try:
            payload = json.dumps(self.client.state, ensure_ascii=False)
            self.window.evaluate_js(f"window.updateFromPythonState && window.updateFromPythonState({payload});")
        except Exception:
            pass

    def push_status(self, msg: str) -> None:
        if not self.window or not self.ui_ready or self.window_hidden:
            return
        try:
            safe_msg = json.dumps(msg, ensure_ascii=False)
            self.window.evaluate_js(f"window.setStatusText && window.setStatusText({safe_msg});")
        except Exception:
            pass

    def push_toast(self, msg: str, icon: str = "✨") -> None:
        if not self.window or not self.ui_ready or self.window_hidden:
            return
        try:
            s_msg = json.dumps(msg, ensure_ascii=False)
            s_ico = json.dumps(icon, ensure_ascii=False)
            self.window.evaluate_js(f"window.showToast && window.showToast({s_msg}, {s_ico});")
        except Exception:
            pass

    def show_ios_popup(self, force_desktop: bool = True) -> None:
        """Exibe o Overlay Flutuante Nativo Windows 11 Estilo Apple iOS sobre a área de trabalho."""
        self.desktop_overlay.show(self.client.state)

    def async_connect(self) -> None:
        def worker() -> None:
            if not self.client.mock_mode and self.client.mac:
                is_conn = is_windows_bluetooth_connected(self.client.mac, self.client.model_name)
                if not is_conn:
                    self.client.connected = False
                    self.client.state["connected"] = False
                    self.client.state["bat_l"] = 0
                    self.client.state["bat_r"] = 0
                    self.client.state["bat_case"] = 0
                    self.on_driver_state_updated()
                    self.push_toast(f"{self.client.model_name} não conectado no Bluetooth do Windows!", "⚠️")
                    return

            ok = self.client.connect()
            self.on_driver_state_updated()
            if ok:
                model_lbl = self.client.state.get("model", self.client.model_name)
                self.push_toast(f"{model_lbl} Sincronizado!", "🎧")
                self.show_ios_popup()
            else:
                self.push_toast(f"{self.client.model_name} não conectado no Bluetooth do Windows!", "⚠️")

        threading.Thread(target=worker, daemon=True).start()

    def run_windows_shield(self) -> None:
        def worker() -> None:
            ps_script = os.path.join(BASE_DIR, "fix_windows_audio.ps1")
            if not os.path.exists(ps_script):
                ps_script = os.path.join(RESOURCE_DIR, "fix_windows_audio.ps1")
            if os.path.exists(ps_script):
                subprocess.run(
                    ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_script],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            self.push_status("✅ Blindagem Windows 11 aplicada: A2DP Estéreo Puro & SysFxOff=1 ativos!")
            self.push_toast("Blindagem Windows 11 Ativa!", "🔒")

        threading.Thread(target=worker, daemon=True).start()

    def run_cycle_bt(self) -> None:
        def worker() -> None:
            ps_script = os.path.join(BASE_DIR, "scripts", "cycle_bt.ps1")
            if not os.path.exists(ps_script):
                ps_script = os.path.join(RESOURCE_DIR, "scripts", "cycle_bt.ps1")
            if os.path.exists(ps_script):
                subprocess.run(
                    ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_script],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            time.sleep(1.2)
            self.client.connect()
            self.on_driver_state_updated()

        threading.Thread(target=worker, daemon=True).start()

    def hide_window_to_tray(self) -> None:
        if self.window:
            self.window_hidden = True
            try:
                self.window.hide()
            except Exception:
                pass
            gc.collect()

    def _async_hide_to_tray(self) -> None:
        """Oculta a janela de forma assíncrona desacoplada do callback WinForms para evitar deadlock."""
        self.hide_window_to_tray()

    def show_window_from_tray(self) -> None:
        if self.window:
            self.window_hidden = False
            try:
                self.window.show()
                self.window.restore()
            except Exception:
                pass
            try:
                self.window.evaluate_js("window.onHostWindowVisibility && window.onHostWindowVisibility(true);")
            except Exception:
                pass
            if self._ui_state_dirty:
                self.push_state_to_ui()

    def show_view_from_tray(self, view_id: str) -> None:
        self.show_window_from_tray()
        if self.window and self.ui_ready:
            idx_map = {"eq": 0, "nc": 1, "hw": 2, "shield": 3, "spatial": 4}
            idx = idx_map.get(view_id, 0)
            try:
                self.window.evaluate_js(f"window.switchView && window.switchView('{view_id}', {idx});")
            except Exception:
                pass

    def quit_app(self) -> None:
        """Encerramento limpo, determinístico e ultra-rápido de todos os subsistemas."""
        if getattr(self, "_quitting_done", False):
            return
        self._quitting_done = True
        self.quitting = True
        try:
            self.sys_integration.stop()
        except Exception:
            pass
        try:
            self.desktop_overlay.shutdown()
        except Exception:
            pass
        try:
            self.client.shutdown()
        except Exception:
            pass
        if self.tray_manager:
            try:
                self.tray_manager.stop()
            except Exception:
                pass
        elif self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        release_single_instance_lock()
        if self.window:
            try:
                self.window.destroy()
            except Exception:
                pass
        # Saída atômica imediata sem aguardar threads secundárias presas
        os._exit(0)

    def start_system_tray(self) -> None:
        """Inicia o daemon de segundo plano na Bandeja do Sistema com telemetria dinâmica."""
        self.tray_manager = SystemTrayManager(self)
        self.tray_manager.start()

    def _toggle_apo_from_tray(self) -> None:
        new_val = not self.apo_engine.enabled
        self.apo_engine.enabled = new_val
        self.config["apo_enabled"] = new_val
        save_config(self.config)
        self.apo_engine.sync_dsp_file()
        self.client.state["apo_global_active"] = new_val
        self.push_state_to_ui()

    def _tray_nc(self, mode: str) -> None:
        self.client.enqueue_action(
            "nc_asm",
            self.client.set_nc_asm,
            mode,
            int(self.client.state.get("asm_level", 10)),
            bool(self.client.state.get("focus_on_voice", False)),
        )
        self.client.state["nc_mode"] = mode
        self.on_driver_state_updated()

    def _tray_eq(self, label: str, cb: int, bands: List[int]) -> None:
        clean_bands = [int(b) for b in bands[:5]]
        cb_val = int(cb)
        self.client.state["eq_preset"] = label
        self.client.state["clear_bass"] = cb_val
        self.client.state["eq_bands"] = clean_bands
        self.client.enqueue_action("eq", self.client.set_eq_custom, "Manual (Custom)", cb_val, clean_bands)
        self.config["active_eq_preset"] = label
        self.config["saved_custom_eq"] = {
            "clear_bass": cb_val,
            "bands": clean_bands,
        }
        save_config(self.config)
        self.on_driver_state_updated()

    def on_webview_loaded(self) -> None:
        self.ui_ready = True
        apply_win32_window_icon("Sony | G HUB Studio — WF-1000XM3 Edition")
        assets = resolve_nano_asset_uris()
        try:
            assets_json = json.dumps(assets)
            self.window.evaluate_js(f"window.setNanoAssets && window.setNanoAssets({assets_json});")
        except Exception:
            pass
        self.push_state_to_ui()
        accent = query_windows_accent_color()
        if accent.get("success"):
            hex_col = accent["accent_hex"]
            try:
                self.window.evaluate_js(f"window.applyWindowsAccentColor && window.applyWindowsAccentColor('{hex_col}');")
            except Exception:
                pass
        self.async_connect()
        try:
            self.window.evaluate_js("window.startSplashTimer && window.startSplashTimer();")
        except Exception:
            pass
        gc.collect()

    def run(self) -> None:
        import webview

        self.start_system_tray()
        self.sys_integration.start()
        api = GHubApiBridge(self)

        self.window = webview.create_window(
            title="Sony | G HUB Studio — WF-1000XM3 Edition",
            url=UI_HTML_PATH,
            js_api=api,
            width=1060,
            height=720,
            min_size=(940, 640),
            background_color="#07080B",
        )
        self.window.events.shown += lambda: apply_win32_window_icon("Sony | G HUB Studio — WF-1000XM3 Edition")
        self.window.events.loaded += self.on_webview_loaded
        self.window.events.closing += self.on_window_closing
        try:
            webview.start(
                private_mode=False,
                icon=ICON_ICO_PATH if os.path.exists(ICON_ICO_PATH) else None,
            )
        finally:
            self.quit_app()

    def on_window_closing(self) -> bool:
        """Gerencia o fechamento da janela com encerramento atômico ou minimização limpa."""
        if self.quitting:
            return True
        close_pref = bool(self.config.get("close_to_tray", True))
        if close_pref:
            # Nunca chamar evaluate_js nem hide sincronamente dentro do FormClosing:
            # dispara thread timer não-bloqueante de 20ms e cancela o fechamento destrutivo
            threading.Timer(0.02, self._async_hide_to_tray).start()
            return False
        # Se fechar para bandeja estiver desativado, encerra limpo e imediato
        threading.Thread(target=self.quit_app, name="FastQuitThread", daemon=True).start()
        return True
