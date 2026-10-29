# -*- coding: utf-8 -*-
"""
Sony Sound Connect PC — Módulo Central da Aplicação
Created by Matheus Veras • Licença: Source-Available Proprietary (Ver LICENSE.md)

Pacote modularizado com arquitetura limpa de produção:
- config: Definições de caminhos, presets de áudio, perfis biométricos e persistência atômica.
- win32_utils: Integrações de baixo nível com Windows 11 (Mutex, DWM Accent Color, Startup, Ícone de Janela, Idioma).
- tray_manager: Gerenciamento dinâmico da bandeja do sistema (LED semântico, telemetria em tempo real, menu contextual).
- rpc_bridge: Ponte RPC fortemente tipada entre a interface Web (HTML/JS/CSS) e os subsistemas Python.
- controller: Orquestrador mestre integrando drivers de fone, APO Global DSP, Overlay iOS e WebView2.
"""

from app.config import (
    ASSETS_DIR,
    BASE_DIR,
    CONFIG_PATH,
    DEFAULT_BIOMETRIC_PROFILES,
    DEFAULT_MAC,
    DEFAULT_PORT,
    GHUB_PRESETS,
    ICON_ICO_PATH,
    ICON_PNG_PATH,
    UI_HTML_PATH,
    is_mock_requested_from_env,
    load_config,
    resolve_nano_asset_uris,
    save_config,
)
from app.controller import SonyGHubController
from app.rpc_bridge import GHubApiBridge
from app.tray_manager import (
    SystemTrayManager,
    compute_battery_bucket,
    create_tray_icon_image,
    format_tray_tooltip,
)
from app.win32_utils import (
    acquire_single_instance_lock,
    apply_win32_window_icon,
    detect_system_language,
    get_windows_run_at_startup,
    query_windows_accent_color,
    release_single_instance_lock,
    set_windows_run_at_startup,
)

__all__ = [
    "BASE_DIR",
    "CONFIG_PATH",
    "ASSETS_DIR",
    "UI_HTML_PATH",
    "ICON_ICO_PATH",
    "ICON_PNG_PATH",
    "DEFAULT_MAC",
    "DEFAULT_PORT",
    "GHUB_PRESETS",
    "DEFAULT_BIOMETRIC_PROFILES",
    "is_mock_requested_from_env",
    "load_config",
    "save_config",
    "resolve_nano_asset_uris",
    "acquire_single_instance_lock",
    "release_single_instance_lock",
    "query_windows_accent_color",
    "set_windows_run_at_startup",
    "get_windows_run_at_startup",
    "detect_system_language",
    "apply_win32_window_icon",
    "SystemTrayManager",
    "create_tray_icon_image",
    "compute_battery_bucket",
    "format_tray_tooltip",
    "GHubApiBridge",
    "SonyGHubController",
]

