# -*- coding: utf-8 -*-
"""
Controlador Central, Orquestrador Multimarca & Ponte DSP Global — Sony Sound Connect PC
Created by Matheus Veras
Licença: Source-Available Proprietary (Ver LICENSE.md)

Arquitetura de Produção Modular:
- Pacote `app/`: Configuração, Win32 Utils, Tray Manager, RPC Bridge e Controller.
- Ecossistema de Drivers Multimarca (`core/drivers/`): Sony MDR V1, Tandem V2 e Universal Windows 11.
- Motor Global Windows 11 (`core/windows_apo_engine.py`): Equalizador Paramétrico + Áudio Espacial 3D Linkwitz.
- Integração de Kernel (`core/system_integration.py`): Zero-Click Auto-Connect via WM_DEVICECHANGE.
- Overlay Flutuante Nativo iOS (`core/ios_desktop_overlay.py`): UpdateLayeredWindow sem roubo de foco.
"""

import ctypes
import sys

try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("MatheusVeras.HeadsetPlusStudio.App")
except Exception:
    pass

# Exportações do pacote `app` para 100% de compatibilidade retroativa com testes e scripts
from app import (
    ASSETS_DIR,
    BASE_DIR,
    CONFIG_PATH,
    DEFAULT_BIOMETRIC_PROFILES,
    DEFAULT_MAC,
    DEFAULT_PORT,
    GHUB_PRESETS,
    GHubApiBridge,
    ICON_ICO_PATH,
    ICON_PNG_PATH,
    SonyGHubController,
    SystemTrayManager,
    UI_HTML_PATH,
    acquire_single_instance_lock,
    apply_win32_window_icon,
    compute_battery_bucket,
    create_tray_icon_image,
    detect_system_language,
    format_tray_tooltip,
    get_windows_run_at_startup,
    is_mock_requested_from_env,
    load_config,
    query_windows_accent_color,
    release_single_instance_lock,
    resolve_nano_asset_uris,
    save_config,
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


def main() -> None:
    """Ponto de entrada principal da aplicação."""
    if not acquire_single_instance_lock():
        sys.exit(0)
    app = SonyGHubController()
    app.run()


if __name__ == "__main__":
    main()
