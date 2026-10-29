# -*- coding: utf-8 -*-
"""
Sony Sound Connect PC — Ponte RPC (JavaScript <-> Python Bridge)
Created by Matheus Veras • Licença: Source-Available Proprietary (Ver LICENSE.md)

Responsabilidades:
- Exposição de interface RPC fortemente tipada ao frontend (window.pywebview.api).
- Intermediação segura entre as chamadas da interface e o SonyGHubController.
- Validação e sanitização de dados recebidos antes de encaminhar aos drivers e DSP.
"""

import time
from typing import Any, Dict, List, Optional

from app.config import DEFAULT_BIOMETRIC_PROFILES, GHUB_PRESETS, save_config
from app.win32_utils import (
    detect_system_language,
    get_windows_run_at_startup,
    query_windows_accent_color,
    set_windows_run_at_startup,
)
from core.autoeq_database import get_brands, search_autoeq
from core.device_detector import list_paired_headsets
from core.system_integration import DEFAULT_AUTOMATION_RULES


class GHubApiBridge:
    """Interface RPC exposta ao frontend `window.pywebview.api` com tipagem estrita."""

    def __init__(self, controller: Any) -> None:
        self._ctrl = controller

    def get_runtime_bootstrap(self) -> Dict[str, Any]:
        """Retorna estado inicial consolidado de configuração, APO, automação, perfis biométricos e Mock."""
        return {
            "mock_mode": self._ctrl.client.mock_mode,
            "auto_profiles_enabled": self._ctrl.sys_integration.auto_profile_enabled,
            "active_eq_preset": self._ctrl.config.get("active_eq_preset", "Audiófilo (Comunidade)"),
            "saved_custom_eq": self._ctrl.config.get("saved_custom_eq", {"clear_bass": 3, "bands": [-1, 2, 4, 4, 2]}),
            "biometric_profiles": self._ctrl.config.get("biometric_profiles", DEFAULT_BIOMETRIC_PROFILES),
            "automation_rules": self._ctrl.sys_integration.get_automation_rules(),
            "apo_status": self._ctrl.apo_engine.get_status(),
            "ghub_presets": list(GHUB_PRESETS.keys()),
            "language": self._ctrl.config.get("language", detect_system_language()),
            "system_language": detect_system_language(),
            "run_at_startup": get_windows_run_at_startup(),
            "close_to_tray": bool(self._ctrl.config.get("close_to_tray", True)),
            "active_device": {
                "name": self._ctrl.client.model_name,
                "mac": self._ctrl.client.mac,
                "brand": self._ctrl.client.brand_name,
                "protocol": self._ctrl.client.PROTOCOL_ID,
            },
        }

    def reconnect(self) -> None:
        self._ctrl.async_connect()

    def set_language(self, lang: str) -> Dict[str, Any]:
        """Persiste o idioma selecionado no config.json."""
        clean_lang = str(lang).strip()
        self._ctrl.config["language"] = clean_lang
        save_config(self._ctrl.config)
        return {"language": clean_lang}

    def get_language(self) -> str:
        return str(self._ctrl.config.get("language", detect_system_language()))

    def get_system_language(self) -> str:
        return detect_system_language()

    def set_run_at_startup(self, enabled: bool) -> Dict[str, Any]:
        """Configura execução automática com o Windows 11."""
        flag = bool(enabled)
        self._ctrl.config["run_at_startup"] = flag
        save_config(self._ctrl.config)
        ok = set_windows_run_at_startup(flag)
        return {"run_at_startup": flag, "success": ok}

    def get_run_at_startup(self) -> Dict[str, Any]:
        return {"run_at_startup": get_windows_run_at_startup()}

    def set_close_to_tray(self, enabled: bool) -> Dict[str, Any]:
        """Configura se o botão 'X' fecha a janela para a bandeja ou encerra o app."""
        flag = bool(enabled)
        self._ctrl.config["close_to_tray"] = flag
        save_config(self._ctrl.config)
        return {"close_to_tray": flag}

    def get_windows_accent_color(self) -> Dict[str, Any]:
        """Obtém a cor de destaque real do Windows 11 para sincronização visual com o tema."""
        return query_windows_accent_color()

    def select_headset_device(self, device: Dict[str, Any]) -> Dict[str, Any]:
        """Alterna dinamicamente entre drivers Sony V1, Sony Tandem V2 e Universal Windows 11."""
        return self._ctrl.switch_headset_driver(device)

    def set_mock_mode(self, enabled: bool) -> Dict[str, Any]:
        flag = bool(enabled)
        self._ctrl.config["mock_mode"] = flag
        cfg_copy = dict(self._ctrl.config)
        cfg_copy["mock_mode"] = False
        save_config(cfg_copy)
        self._ctrl.toggle_mock_mode(flag)
        return {"mock_mode": flag}

    def set_nc_asm(self, mode: str, asm_level: int, focus_voice: bool) -> None:
        self._ctrl.client.enqueue_action(
            "nc_asm",
            self._ctrl.client.set_nc_asm,
            str(mode),
            int(asm_level),
            bool(focus_voice),
        )
        self._ctrl.push_status(f"Controle Acústico alterado para: {mode}")

    def set_eq_custom(self, preset_name: str, clear_bass: int, bands: List[int]) -> None:
        clean_bands = [int(b) for b in list(bands)[:5]]
        cb_val = int(clear_bass)
        self._ctrl.client.enqueue_action(
            "eq",
            self._ctrl.client.set_eq_custom,
            str(preset_name),
            cb_val,
            clean_bands,
        )
        self._ctrl.config["active_eq_preset"] = str(preset_name)
        self._ctrl.config["saved_custom_eq"] = {
            "clear_bass": cb_val,
            "bands": clean_bands,
        }
        save_config(self._ctrl.config)
        self._ctrl.push_status(f"Equalizador DSP sincronizado: Clear Bass {cb_val:+d} dB | Bandas {clean_bands}")

    def set_eq_preset_only(self, preset_name: str) -> None:
        self._ctrl.client.enqueue_action(
            "eq",
            self._ctrl.client.set_eq_preset_only,
            str(preset_name),
        )
        self._ctrl.push_status(f"Preset de hardware ativado: {preset_name}")

    def save_user_preset(self, clear_bass: int, bands: List[int]) -> None:
        self._ctrl.config["saved_custom_eq"] = {
            "clear_bass": int(clear_bass),
            "bands": [int(b) for b in list(bands)[:5]],
        }
        save_config(self._ctrl.config)
        self._ctrl.push_status("💾 Perfil personalizado salvo em config.json!")

    # --- Perfis Biométricos ISO 226 ---
    def get_biometric_profiles(self) -> List[Dict[str, Any]]:
        return list(self._ctrl.config.get("biometric_profiles", DEFAULT_BIOMETRIC_PROFILES))

    def save_biometric_profile(
        self,
        name: str,
        clear_bass: int,
        bands: List[int],
        thresholds: Optional[List[float]] = None,
    ) -> List[Dict[str, Any]]:
        clean_name = (name or "Perfil Biométrico").strip()[:42]
        slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in clean_name).strip("-") or f"bio-{int(time.time())}"
        profiles: List[Dict[str, Any]] = list(self._ctrl.config.get("biometric_profiles", DEFAULT_BIOMETRIC_PROFILES))

        entry: Dict[str, Any] = {
            "id": slug,
            "name": clean_name,
            "clear_bass": max(-10, min(10, int(clear_bass))),
            "bands": [max(-10, min(10, int(b))) for b in list(bands)[:5]],
            "thresholds": [round(float(t), 1) for t in (thresholds or [])[:6]],
        }

        replaced = False
        for idx, existing in enumerate(profiles):
            if existing.get("id") == slug or existing.get("name", "").lower() == clean_name.lower():
                profiles[idx] = entry
                replaced = True
                break
        if not replaced:
            profiles.append(entry)

        self._ctrl.config["biometric_profiles"] = profiles
        save_config(self._ctrl.config)
        return profiles

    def delete_biometric_profile(self, profile_id: str) -> List[Dict[str, Any]]:
        profiles: List[Dict[str, Any]] = [
            p for p in self._ctrl.config.get("biometric_profiles", []) if p.get("id") != profile_id
        ]
        if not profiles:
            profiles = list(DEFAULT_BIOMETRIC_PROFILES)
        self._ctrl.config["biometric_profiles"] = profiles
        save_config(self._ctrl.config)
        return profiles

    # --- Motor DSP Global Windows 11 (Equalizer APO Bridge) ---
    def get_apo_status(self) -> Dict[str, Any]:
        return self._ctrl.apo_engine.get_status()

    def set_apo_enabled(self, enabled: bool) -> Dict[str, Any]:
        self._ctrl.apo_engine.enabled = bool(enabled)
        self._ctrl.config["apo_enabled"] = bool(enabled)
        save_config(self._ctrl.config)
        self._ctrl.apo_engine.sync_dsp_file()
        self._ctrl.client.state["apo_global_active"] = bool(enabled)
        return self._ctrl.apo_engine.get_status()

    def link_equalizer_apo(self) -> Dict[str, Any]:
        return self._ctrl.apo_engine.try_link_into_equalizer_apo()

    def sync_spatial_to_apo(self, enabled: bool, mode: str, width: int) -> Dict[str, Any]:
        self._ctrl.config["spatial_enabled"] = bool(enabled)
        self._ctrl.config["spatial_mode"] = str(mode)
        self._ctrl.config["crossfeed_width"] = int(width)
        save_config(self._ctrl.config)
        return self._ctrl.apo_engine.update_spatial(bool(enabled), str(mode), int(width))

    # --- Saúde Auditiva & Dosímetro dB SPL (CoreAudio COM) ---
    def get_hearing_safety_telemetry(self) -> Dict[str, Any]:
        st = self._ctrl.client.state
        res = self._ctrl.hearing_safety.sample(
            clear_bass=int(st.get("clear_bass", 0)),
            eq_bands=list(st.get("eq_bands", [0, 0, 0, 0, 0])),
        )
        if res.get("trigger_warning"):
            self._ctrl.push_toast("Alerta OMS: Exposição acima de 85 dB SPL contínua!", "⚠️")
        return res

    # --- Automação Editável de Combos por Aplicativo ---
    def get_automation_rules(self) -> List[Dict[str, Any]]:
        return self._ctrl.sys_integration.get_automation_rules()

    def save_automation_rule(self, rule: Dict[str, Any]) -> List[Dict[str, Any]]:
        rules = self._ctrl.sys_integration.upsert_automation_rule(rule)
        self._ctrl.config["automation_rules"] = rules
        save_config(self._ctrl.config)
        return rules

    def delete_automation_rule(self, exe_name: str) -> List[Dict[str, Any]]:
        rules = self._ctrl.sys_integration.remove_automation_rule(exe_name)
        self._ctrl.config["automation_rules"] = rules
        save_config(self._ctrl.config)
        return rules

    def reset_automation_rules(self) -> List[Dict[str, Any]]:
        rules = self._ctrl.sys_integration.set_automation_rules(DEFAULT_AUTOMATION_RULES)
        self._ctrl.config["automation_rules"] = rules
        save_config(self._ctrl.config)
        return rules

    # --- Preferências de Hardware & Sistema ---
    def set_connection_mode(self, stable_priority: bool) -> None:
        self._ctrl.client.enqueue_action("conn_mode", self._ctrl.client.set_connection_mode, bool(stable_priority))

    def set_dsee_hx(self, enabled: bool) -> None:
        self._ctrl.client.enqueue_action("dsee", self._ctrl.client.set_dsee_hx, bool(enabled))

    def set_wearing_pause(self, enabled: bool) -> None:
        self._ctrl.client.enqueue_action("wearing", self._ctrl.client.set_wearing_pause, bool(enabled))

    def set_auto_power_off(self, option_name: str) -> None:
        self._ctrl.client.enqueue_action("auto_off", self._ctrl.client.set_auto_power_off, str(option_name))

    def set_touch_sensors(self, left_name: str, right_name: str) -> None:
        self._ctrl.client.enqueue_action("touch", self._ctrl.client.set_touch_sensors, str(left_name), str(right_name))

    def update_mac_address(self, new_mac: str) -> None:
        if new_mac:
            self._ctrl.config["mac_address"] = new_mac
            save_config(self._ctrl.config)
            self._ctrl.client.mac = new_mac
            self._ctrl.client.state["mac"] = new_mac
            self._ctrl.async_connect()

    def power_off_headphones(self) -> None:
        self._ctrl.client.enqueue_action("power_off", self._ctrl.client.power_off_headphones)

    def reapply_windows_audio_fix(self) -> None:
        self._ctrl.run_windows_shield()

    def cycle_bluetooth(self) -> None:
        self._ctrl.run_cycle_bt()

    def hide_to_tray(self) -> None:
        self._ctrl.hide_window_to_tray()

    def get_detected_headsets(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        return list_paired_headsets(force_refresh=bool(force_refresh))

    def trigger_ios_popup(self) -> None:
        self._ctrl.show_ios_popup(force_desktop=False)

    def trigger_desktop_ios_overlay(self) -> Dict[str, Any]:
        """Dispara explicitamente o Overlay Flutuante Nativo Windows 11 (UpdateLayeredWindow)."""
        self._ctrl.desktop_overlay.show(self._ctrl.client.state)
        return {"ok": True}

    def search_autoeq_profiles(self, query: str = "", brand: str = "all") -> List[Dict[str, Any]]:
        return search_autoeq(query, brand)

    def get_autoeq_brands(self) -> List[str]:
        return get_brands()

    def apply_autoeq_profile(self, name: str, clear_bass: int, bands: List[int]) -> None:
        self._ctrl._tray_eq(f"AutoEq: {name}", int(clear_bass), [int(b) for b in list(bands)[:5]])
        self._ctrl.push_toast(f"Calibração AutoEq: {name}", "🎯")

    def set_auto_profile_enabled(self, enabled: bool) -> None:
        self._ctrl.sys_integration.auto_profile_enabled = bool(enabled)
        self._ctrl.config["auto_profiles_enabled"] = bool(enabled)
        save_config(self._ctrl.config)
        status = "ativada" if enabled else "desativada"
        self._ctrl.push_toast(f"Troca automática de perfis {status}!", "⚡")

