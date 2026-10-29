# -*- coding: utf-8 -*-
"""
Sony Sound Connect PC — Gerenciador de Configuração & Constantes Globais
Created by Matheus Veras • Licença: Source-Available Proprietary (Ver LICENSE.md)

Responsabilidades:
- Centralização de caminhos de arquivos e diretórios do sistema.
- Definição de perfis de equalização de fábrica (G HUB Presets).
- Definição de perfis biométricos auditivos padrão (ISO 226).
- Carregamento e salvamento atômico de configurações (config.json) com fallback resiliente.
- Mapeamento dinâmico de recursos gráficos 3D locais (resolve_nano_asset_uris).
"""

import json
import os
import sys
from typing import Any, Dict, List, Tuple

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    RESOURCE_DIR: str = getattr(sys, "_MEIPASS")
    APP_DIR: str = os.path.dirname(sys.executable)
else:
    RESOURCE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    APP_DIR = RESOURCE_DIR

BASE_DIR: str = APP_DIR
CONFIG_PATH: str = os.path.join(APP_DIR, "config.json")
ASSETS_DIR: str = os.path.join(RESOURCE_DIR, "assets")
UI_HTML_PATH: str = os.path.join(RESOURCE_DIR, "index.html")
ICON_ICO_PATH: str = os.path.join(ASSETS_DIR, "app_icon.ico")
ICON_PNG_PATH: str = os.path.join(ASSETS_DIR, "app_icon.png")

DEFAULT_MAC: str = "14:3F:A6:5D:DF:D5"
DEFAULT_PORT: int = 9

GHUB_PRESETS: Dict[str, Tuple[int, List[int]]] = {
    "Gaming FPS (Passos)": (-2, [0, 3, 6, 5, 2]),
    "Audiófilo (Comunidade)": (3, [-1, 1, 2, 4, 3]),
    "Empolgado (Meu Perfil)": (8, [-1, 1, 0, 3, 5]),
    "Voz & Podcast": (-1, [-2, 3, 4, 1, -1]),
    "Cinema Sub-Bass": (9, [-1, 0, 1, 2, 4]),
}

DEFAULT_BIOMETRIC_PROFILES: List[Dict[str, Any]] = [
    {
        "id": "matheus-dia",
        "name": "Matheus Dia (ISO 226 Reference)",
        "clear_bass": 2,
        "bands": [0, 1, 3, 2, 2],
        "thresholds": [-17, -24, -28, -31, -23, -15],
    },
    {
        "id": "matheus-noite",
        "name": "Matheus Noite / Foco (Low-SPL)",
        "clear_bass": 3,
        "bands": [1, 0, 2, 2, 3],
        "thresholds": [-15, -23, -28, -30, -22, -13],
    },
]


def is_mock_requested_from_env() -> bool:
    """Detecta ativação do modo de simulação virtual via CLI (--mock) ou variável MOCK_DEVICE=1."""
    env_val = os.environ.get("MOCK_DEVICE", "").strip().lower()
    if env_val in ("1", "true", "yes", "on"):
        return True
    return "--mock" in sys.argv


def load_config() -> Dict[str, Any]:
    """Carrega config.json com valores padrão seguros, regras de automação e perfis biométricos."""
    from app.win32_utils import detect_system_language
    from core.system_integration import DEFAULT_AUTOMATION_RULES

    detected_sys_lang = detect_system_language()
    cfg: Dict[str, Any] = {
        "mac_address": DEFAULT_MAC,
        "rfcomm_port": DEFAULT_PORT,
        "active_model": "WF-1000XM3",
        "active_brand": "Sony",
        "active_protocol": "sony_mdr",
        "auto_profiles_enabled": True,
        "mock_mode": False,
        "apo_enabled": True,
        "spatial_enabled": True,
        "spatial_mode": "nearfield",
        "crossfeed_width": 65,
        "active_eq_preset": "Audiófilo (Comunidade)",
        "saved_custom_eq": {"clear_bass": 3, "bands": [-1, 2, 4, 4, 2]},
        "biometric_profiles": list(DEFAULT_BIOMETRIC_PROFILES),
        "automation_rules": list(DEFAULT_AUTOMATION_RULES),
        "language": detected_sys_lang,
        "run_at_startup": False,
        "close_to_tray": True,
    }
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    cfg.update(data)
        except Exception:
            pass
    if not isinstance(cfg.get("biometric_profiles"), list) or not cfg["biometric_profiles"]:
        cfg["biometric_profiles"] = list(DEFAULT_BIOMETRIC_PROFILES)
    if not isinstance(cfg.get("automation_rules"), list) or not cfg["automation_rules"]:
        cfg["automation_rules"] = list(DEFAULT_AUTOMATION_RULES)
    return cfg


def save_config(cfg: Dict[str, Any]) -> None:
    """Persiste as configurações do usuário de forma atômica em disco (sempre mantendo mock_mode=False)."""
    try:
        to_save = dict(cfg)
        to_save["mock_mode"] = False
        tmp_path = CONFIG_PATH + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(to_save, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, CONFIG_PATH)
    except Exception:
        pass


def resolve_nano_asset_uris() -> Dict[str, str]:
    """Resolve caminhos relativos dos renders 3D diretamente para o WebView2 (zero duplicação Base64)."""
    mapping: Dict[str, List[str]] = {
        "l": ["earbud_l_clean.png", "earbud_l_nano.png", "earbud_l.png"],
        "r": ["earbud_r_clean.png", "earbud_r_nano.png", "earbud_r.png"],
        "c": ["case_clean.png", "case_nano.png", "earbud_case.png"],
        "icon": ["app_icon_web.png", "app_icon.png"],
    }
    out: Dict[str, str] = {"l": "", "r": "", "c": "", "icon": ""}
    for key, candidates in mapping.items():
        for fname in candidates:
            fpath = os.path.join(ASSETS_DIR, fname)
            if os.path.exists(fpath):
                out[key] = f"assets/{fname}"
                break
    return out
