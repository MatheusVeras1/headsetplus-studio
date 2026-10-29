"""
Motor DSP Global para Windows 11 (Equalizer APO & Linkwitz Crossfeed Bridge) — Sony Sound Connect PC
Autor: Matheus Veras
Licença: Source-Available Proprietary (Ver LICENSE.md)

Gera e sincroniza em tempo real matrizes Biquad paramétricas de 6 bandas + Crossfeed 3D Linkwitz/Chu-Moy
diretamente para o motor global de áudio do Windows 11 (Equalizer APO / AudioDG.exe), permitindo que
qualquer fone (Sony, realme, AirPods, Galaxy Buds, headsets USB/P2) tenha processamento DSP global.
"""

import math
import os
import threading
from typing import Any, Dict, List, Optional

APO_DEFAULT_CONFIG_DIR = r"C:\Program Files\EqualizerAPO\config"
APO_MAIN_CONFIG_FILE = os.path.join(APO_DEFAULT_CONFIG_DIR, "config.txt")
APO_INCLUDE_FILENAME = "headsetplus_studio_dsp.txt"

SPATIAL_APO_MODES: Dict[str, Dict[str, float]] = {
    "nearfield": {"cutoff_hz": 700.0, "delay_ms": 0.28, "base_cross_db": -6.0},
    "hifi": {"cutoff_hz": 620.0, "delay_ms": 0.34, "base_cross_db": -5.2},
    "esports": {"cutoff_hz": 880.0, "delay_ms": 0.22, "base_cross_db": -6.8},
}


class WindowsApoEngine:
    """
    Gerencia a geração atômica e integração de filtros DSP globais no Windows 11.
    Opera com fallback local transparente caso o Equalizer APO não esteja instalado ou exija UAC.
    """

    def __init__(self, app_base_dir: str) -> None:
        self._base_dir = app_base_dir
        self._local_export_dir = os.path.join(app_base_dir, "apo_dsp")
        self._local_dsp_path = os.path.join(self._local_export_dir, APO_INCLUDE_FILENAME)
        self._system_dsp_path = os.path.join(APO_DEFAULT_CONFIG_DIR, APO_INCLUDE_FILENAME)
        self._lock = threading.Lock()

        self.enabled: bool = True
        self.clear_bass: int = 0
        self.eq_bands: List[int] = [0, 0, 0, 0, 0]
        self.spatial_enabled: bool = True
        self.spatial_mode: str = "nearfield"
        self.crossfeed_width: int = 65
        self.active_profile_label: str = "Harman Reference"

    def is_equalizer_apo_installed(self) -> bool:
        """Verifica se o diretório de configuração do Equalizer APO existe no Windows 11."""
        return os.path.isdir(APO_DEFAULT_CONFIG_DIR)

    def is_linked_in_main_config(self) -> bool:
        """Verifica se `Include: sony_sound_connect_dsp.txt` já está ativo no config.txt do Equalizer APO."""
        if not os.path.exists(APO_MAIN_CONFIG_FILE):
            return False
        try:
            with open(APO_MAIN_CONFIG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return APO_INCLUDE_FILENAME.lower() in content.lower()
        except Exception:
            return False

    def try_link_into_equalizer_apo(self) -> Dict[str, Any]:
        """
        Tenta registrar automaticamente `Include: sony_sound_connect_dsp.txt` no Equalizer APO
        e sincronizar o filtro DSP atual.
        """
        installed = self.is_equalizer_apo_installed()
        sync_res = self.sync_dsp_file()

        if not installed:
            return {
                "installed": False,
                "linked": False,
                "active_path": sync_res["written_path"],
                "message": "Equalizer APO não detectado em C:\\Program Files\\EqualizerAPO. Filtro salvo localmente em apo_dsp/ para importação.",
            }

        linked = self.is_linked_in_main_config()
        if not linked and os.path.exists(APO_MAIN_CONFIG_FILE):
            try:
                with open(APO_MAIN_CONFIG_FILE, "a", encoding="utf-8") as f:
                    f.write(f"\n# Sony Sound Connect PC (Created by Matheus Veras)\nInclude: {APO_INCLUDE_FILENAME}\n")
                linked = True
            except PermissionError:
                return {
                    "installed": True,
                    "linked": False,
                    "active_path": sync_res["written_path"],
                    "message": "Equalizer APO detectado! Adicione 'Include: sony_sound_connect_dsp.txt' no Configuration Editor (ou execute como Admin).",
                }
            except Exception:
                pass

        return {
            "installed": True,
            "linked": linked,
            "active_path": sync_res["written_path"],
            "message": "DSP Global Windows 11 sincronizado ao vivo com Equalizer APO!" if linked else "Filtro DSP exportado com sucesso.",
        }

    def get_status(self) -> Dict[str, Any]:
        installed = self.is_equalizer_apo_installed()
        linked = self.is_linked_in_main_config() if installed else False
        return {
            "enabled": self.enabled,
            "apo_installed": installed,
            "apo_linked": linked,
            "local_path": self._local_dsp_path,
            "system_path": self._system_dsp_path if installed else "",
            "spatial_enabled": self.spatial_enabled,
            "spatial_mode": self.spatial_mode,
            "crossfeed_width": self.crossfeed_width,
        }

    def update_eq(self, label: str, clear_bass: int, bands: List[int]) -> Dict[str, Any]:
        with self._lock:
            self.active_profile_label = label
            self.clear_bass = max(-10, min(10, int(clear_bass)))
            self.eq_bands = [max(-10, min(10, int(b))) for b in list(bands)[:5]]
            while len(self.eq_bands) < 5:
                self.eq_bands.append(0)
        return self.sync_dsp_file()

    def update_spatial(self, enabled: bool, mode: str, width_pct: int) -> Dict[str, Any]:
        with self._lock:
            self.spatial_enabled = bool(enabled)
            if mode in SPATIAL_APO_MODES:
                self.spatial_mode = mode
            self.crossfeed_width = max(0, min(100, int(width_pct)))
        return self.sync_dsp_file()

    def build_apo_script(self) -> str:
        """Gera script nativo Equalizer APO com anti-clipping Preamp, 6 bandas Biquad e Crossfeed Linkwitz."""
        lines: List[str] = [
            "# =====================================================================",
            "# Sony Sound Connect PC — Global Windows 11 DSP Engine",
            "# Created by Matheus Veras (Source-Available Proprietary — LICENSE.md)",
            f"# Active Profile: {self.active_profile_label}",
            "# =====================================================================",
        ]

        if not self.enabled:
            lines.append("# DSP Bypass Ativo (0.0 dB Flat)")
            lines.append("Preamp: 0.0 dB")
            return "\n".join(lines) + "\n"

        all_gains = [self.clear_bass] + self.eq_bands
        max_boost = max([0] + all_gains)
        preamp_db = -round(max_boost * 0.85, 2) if max_boost > 0 else 0.0

        lines.append(f"Preamp: {preamp_db:.2f} dB")
        lines.append("")
        lines.append("# --- 6-Band Parametric & Clear Bass Filter Bank ---")
        lines.append(f"Filter 1: ON LSC Fc 95 Hz Gain {self.clear_bass:.1f} dB Q 0.71")

        band_specs = [
            (2, "PK", 400, 1.35, self.eq_bands[0]),
            (3, "PK", 1000, 1.41, self.eq_bands[1]),
            (4, "PK", 2500, 1.41, self.eq_bands[2]),
            (5, "PK", 6300, 1.45, self.eq_bands[3]),
            (6, "HSC", 12500, 0.75, self.eq_bands[4]),
        ]
        for idx, ftype, fc, q_val, gain in band_specs:
            lines.append(f"Filter {idx}: ON {ftype} Fc {fc} Hz Gain {gain:.1f} dB Q {q_val:.2f}")

        if self.spatial_enabled and self.crossfeed_width > 0:
            spec = SPATIAL_APO_MODES.get(self.spatial_mode, SPATIAL_APO_MODES["nearfield"])
            w_norm = self.crossfeed_width / 100.0
            ref_lin = 10.0 ** (spec["base_cross_db"] / 20.0)
            cross_lin = min(0.58, ref_lin * (w_norm / 0.65))
            direct_lin = 1.0 / math.sqrt(1.0 + cross_lin * cross_lin)
            shelf_db = round(1.8 * min(1.25, w_norm / 0.65), 2)

            lines.extend([
                "",
                f"# --- Linkwitz / Chu-Moy 3D Crossfeed Matrix ({self.spatial_mode.upper()} @ {self.crossfeed_width}%) ---",
                "Copy: L_DIR=L R_DIR=R L_X=L R_X=R",
                "Channel: L_DIR R_DIR",
                f"Filter 7: ON HSC Fc 720 Hz Gain {shelf_db:.2f} dB Q 0.71",
                "Channel: L_X R_X",
                f"Filter 8: ON LPQ Fc {spec['cutoff_hz']:.0f} Hz Q 0.7071",
                f"Delay: {spec['delay_ms']:.2f} ms",
                f"Copy: L={direct_lin:.4f}*L_DIR+{cross_lin:.4f}*R_X R={direct_lin:.4f}*R_DIR+{cross_lin:.4f}*L_X",
                "Channel: all",
            ])

        return "\n".join(lines) + "\n"

    def sync_dsp_file(self) -> Dict[str, Any]:
        """Grava atomicamente o script DSP na pasta local e, se acessível, na pasta do Equalizer APO."""
        script_text = self.build_apo_script()
        os.makedirs(self._local_export_dir, exist_ok=True)
        written_path = self._local_dsp_path

        try:
            tmp_local = self._local_dsp_path + ".tmp"
            with open(tmp_local, "w", encoding="utf-8") as f:
                f.write(script_text)
            os.replace(tmp_local, self._local_dsp_path)
        except Exception:
            pass

        if self.is_equalizer_apo_installed():
            try:
                tmp_sys = self._system_dsp_path + ".tmp"
                with open(tmp_sys, "w", encoding="utf-8") as f:
                    f.write(script_text)
                os.replace(tmp_sys, self._system_dsp_path)
                written_path = self._system_dsp_path
            except Exception:
                pass

        return {"ok": True, "written_path": written_path}
