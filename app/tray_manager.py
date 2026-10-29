# -*- coding: utf-8 -*-
"""
Sony Sound Connect PC — Gerenciador da Bandeja do Sistema (Windows 11 System Tray)
Created by Matheus Veras • Licença: Source-Available Proprietary (Ver LICENSE.md)

Responsabilidades:
- Renderização de ícone 64x64 com LED semântico de bateria em cache (Verde, Âmbar, Vermelho, Cinza).
- Formatação de Tooltip dinâmico rico com telemetria de bateria e cancelamento de ruído (<128 chars).
- Construção do menu de contexto nativo com atalhos de equalização, modos de ruído e DSP.
- Execução não-bloqueante em thread secundária daemon.
"""

import os
import threading
from typing import Any, Callable, Dict, List, Optional
from PIL import Image, ImageDraw

from app.config import ASSETS_DIR, ICON_PNG_PATH

_TRAY_ICON_CACHE: Dict[str, Image.Image] = {}
_TRAY_BASE_64: Optional[Image.Image] = None


def _get_base_tray_64() -> Image.Image:
    """Carrega ou desenha o ícone base 64x64 da aplicação com canal alpha transparente."""
    global _TRAY_BASE_64
    if _TRAY_BASE_64 is not None:
        return _TRAY_BASE_64
    for candidate in [
        os.path.join(ASSETS_DIR, "app_icon_web.png"),
        ICON_PNG_PATH,
        os.path.join(ASSETS_DIR, "earbud_l_clean.png"),
    ]:
        if os.path.exists(candidate):
            try:
                with Image.open(candidate) as raw_img:
                    _TRAY_BASE_64 = raw_img.convert("RGBA").resize((64, 64), Image.Resampling.LANCZOS)
                    return _TRAY_BASE_64
            except Exception:
                pass

    img = Image.new("RGBA", (64, 64), (12, 15, 22, 255))
    d = ImageDraw.Draw(img)
    d.ellipse([4, 4, 60, 60], fill=(18, 22, 32, 255), outline=(197, 160, 89, 255), width=4)
    d.ellipse([18, 18, 46, 46], fill=(0, 229, 255, 255))
    _TRAY_BASE_64 = img
    return _TRAY_BASE_64


def create_tray_icon_image(badge_bucket: str = "good") -> Image.Image:
    """
    Retorna ícone 64x64 da Bandeja do Sistema com LED semântico de status/bateria em cache
    ('good' = Verde, 'medium' = Âmbar, 'critical' = Vermelho <20%, 'disconnected' = Cinza).
    """
    if badge_bucket in _TRAY_ICON_CACHE:
        return _TRAY_ICON_CACHE[badge_bucket]

    base = _get_base_tray_64().copy()
    palette = {
        "good": (16, 185, 129, 255),
        "medium": (245, 158, 11, 255),
        "critical": (239, 68, 68, 255),
        "disconnected": (100, 116, 139, 255),
    }
    dot_color = palette.get(badge_bucket, palette["good"])
    draw = ImageDraw.Draw(base)
    draw.ellipse([43, 43, 62, 62], fill=(7, 8, 11, 245))
    draw.ellipse([46, 46, 59, 59], fill=dot_color)
    _TRAY_ICON_CACHE[badge_bucket] = base
    return base


def compute_battery_bucket(state: Dict[str, Any]) -> str:
    """Classifica a faixa de bateria atual para o LED semântico da bandeja."""
    if not state.get("connected"):
        return "disconnected"
    vals = [int(state.get("bat_l") or 0), int(state.get("bat_r") or 0)]
    active_vals = [v for v in vals if v > 0]
    if not active_vals:
        return "good"
    lowest = min(active_vals)
    if lowest < 20:
        return "critical"
    if lowest < 35:
        return "medium"
    return "good"


def format_tray_tooltip(state: Dict[str, Any]) -> str:
    """Formata tooltip rico (< 127 chars Win32 szTip) com telemetria em tempo real."""
    if not state.get("connected"):
        return "Sony Sound Connect PC • Standby (Auto-Connect Ativo)"
    model = str(state.get("model") or "Headset")[:28]
    bl = int(state.get("bat_l") or 0)
    br = int(state.get("bat_r") or 0)
    bc = int(state.get("bat_case") or 0)
    nc = str(state.get("nc_mode") or "ANC")
    proto = str(state.get("protocol") or "sony_mdr")

    if proto.startswith("sony_mdr"):
        case_part = f" | Case:{bc}%" if bc > 0 else ""
        tip = f"{model} • L:{bl}% R:{br}%{case_part} • {nc}"
    else:
        bat_part = f"Bat:{bl}%" if bl > 0 else "APO Global"
        tip = f"{model} • {bat_part} • 3D DSP Ativo"
    return tip[:126]


class SystemTrayManager:
    """Controlador do ciclo de vida e eventos da bandeja do sistema Windows 11."""

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.tray_icon: Optional[Any] = None
        self._last_bucket: str = ""
        self._last_tip: str = ""

    def start(self) -> None:
        """Inicia a bandeja do sistema em thread daemon assíncrona."""
        try:
            import pystray
            from pystray import MenuItem as item

            ctrl = self.controller
            menu = pystray.Menu(
                item("🎧 Abrir Sony | G HUB Studio", lambda: ctrl.show_window_from_tray(), default=True),
                item(
                    "🪟 Overlay Flutuante iOS (Desktop)",
                    lambda: ctrl.desktop_overlay.show(ctrl.client.state),
                ),
                item("🌌 Áudio Espacial 3D (Crossfeed)", lambda: ctrl.show_view_from_tray("spatial")),
                item("🧬 Teste Auditivo Biométrico", lambda: ctrl.show_view_from_tray("spatial")),
                pystray.Menu.SEPARATOR,
                item("🛡️ Modo: Cancelamento (ANC)", lambda: ctrl._tray_nc("ANC")),
                item("🌬️ Modo: Redução de Vento", lambda: ctrl._tray_nc("Vento")),
                item("🔊 Modo: Som Ambiente", lambda: ctrl._tray_nc("Ambiente")),
                pystray.Menu.SEPARATOR,
                item("⭐ EQ: Preset Audiófilo", lambda: ctrl._tray_eq("Audiófilo", 3, [-1, 2, 4, 4, 2])),
                item("🔥 EQ: Meu Perfil Empolgado", lambda: ctrl._tray_eq("Empolgado", 8, [-1, 1, 0, 3, 5])),
                item("🎮 EQ: Gaming FPS (Passos)", lambda: ctrl._tray_eq("Gaming FPS", -2, [0, 3, 6, 5, 2])),
                pystray.Menu.SEPARATOR,
                item(
                    "🎛️ DSP Global Windows 11 (APO)",
                    lambda: ctrl._toggle_apo_from_tray(),
                    checked=lambda _: ctrl.apo_engine.enabled,
                ),
                item(
                    "🤖 Modo Simulação Virtual (Mock)",
                    lambda: ctrl.toggle_mock_mode(),
                    checked=lambda _: ctrl.client.mock_mode,
                ),
                item("🔒 Blindar Áudio Windows 11", lambda: ctrl.run_windows_shield()),
                item("🔄 Reconectar Bluetooth", lambda: ctrl.async_connect()),
                pystray.Menu.SEPARATOR,
                item("❌ Encerrar Completamente", lambda: ctrl.quit_app()),
            )

            init_bucket = compute_battery_bucket(ctrl.client.state)
            init_tip = format_tray_tooltip(ctrl.client.state)
            self._last_bucket = init_bucket
            self._last_tip = init_tip

            self.tray_icon = pystray.Icon(
                "sony_ghub_studio",
                create_tray_icon_image(init_bucket),
                init_tip,
                menu,
            )
            # Conecta o tray_icon no controller para compatibilidade
            ctrl.tray_icon = self.tray_icon
            threading.Thread(target=self.tray_icon.run, name="SonySystemTray", daemon=True).start()
        except Exception:
            pass

    def refresh_telemetry(self, state: Dict[str, Any]) -> None:
        """Atualiza tooltip e LED semântico apenas se houver alteração de estado."""
        if not self.tray_icon:
            return
        new_tip = format_tray_tooltip(state)
        new_bucket = compute_battery_bucket(state)

        try:
            if new_tip != self._last_tip:
                self._last_tip = new_tip
                self.tray_icon.title = new_tip
            if new_bucket != self._last_bucket:
                self._last_bucket = new_bucket
                self.tray_icon.icon = create_tray_icon_image(new_bucket)
        except Exception:
            pass

    def notify(self, message: str, title: str = "Sony Sound Connect PC") -> None:
        """Emite notificação visual na área de notificação do Windows."""
        if self.tray_icon:
            try:
                self.tray_icon.notify(message, title)
            except Exception:
                pass

    def stop(self) -> None:
        """Encerra a instância da bandeja."""
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None

