"""
Monitor de Saúde Auditiva & Dosímetro dB SPL (Estilo Apple iOS Headphone Safety) — HeadsetPlus Studio
Autor: Matheus Veras
Licença: Source-Available Proprietary (Ver LICENSE.md)

Integra-se diretamente à API COM CoreAudio do Windows 11 (`IMMDeviceEnumerator`,
`IAudioEndpointVolume` e `IAudioMeterInformation`) via `ctypes` puro (zero dependências externas)
para estimar o nível de pressão sonora em tempo real (dB SPL) e a dose diária segura OMS / ITU-T H.870.
"""

import ctypes
import ctypes.wintypes
import math
import time
from typing import Any, Dict, List, Optional, Tuple

ole32 = ctypes.WinDLL("ole32", use_last_error=True)

CLSCTX_ALL = 23
COINIT_MULTITHREADED = 0x0
E_RENDER = 0
E_MULTIMEDIA = 1


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_ulong),
        ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort),
        ("Data4", ctypes.c_ubyte * 8),
    ]

    @classmethod
    def from_str(cls, guid_str: str) -> "GUID":
        s = guid_str.strip("{}").replace("-", "")
        d1 = int(s[0:8], 16)
        d2 = int(s[8:12], 16)
        d3 = int(s[12:16], 16)
        d4 = (ctypes.c_ubyte * 8)(*[int(s[16 + i * 2 : 18 + i * 2], 16) for i in range(8)])
        return cls(d1, d2, d3, d4)


CLSID_MMDeviceEnumerator = GUID.from_str("{BCDE0395-E52F-467C-8E3D-C4579291692E}")
IID_IMMDeviceEnumerator = GUID.from_str("{A95664D2-9614-4F35-A746-DE8DB63617E6}")
IID_IAudioEndpointVolume = GUID.from_str("{5CDF2C82-841E-4546-9722-0CF74078229A}")
IID_IAudioMeterInformation = GUID.from_str("{C02216F6-8C67-4B5B-9D00-D008E73E0064}")

ole32.CoInitializeEx.argtypes = [ctypes.c_void_p, ctypes.wintypes.DWORD]
ole32.CoInitializeEx.restype = ctypes.HRESULT
ole32.CoCreateInstance.argtypes = [
    ctypes.POINTER(GUID),
    ctypes.c_void_p,
    ctypes.wintypes.DWORD,
    ctypes.POINTER(GUID),
    ctypes.POINTER(ctypes.c_void_p),
]
ole32.CoCreateInstance.restype = ctypes.c_long


def _com_release(ptr: ctypes.c_void_p) -> None:
    if ptr and ptr.value:
        vtable = ctypes.cast(ptr, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
        release_fn = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)(vtable[2])
        release_fn(ptr)


def read_windows_coreaudio_levels() -> Tuple[float, float, bool]:
    """
    Lê instantaneamente (< 0.1 ms) via COM CoreAudio do Windows 11:
    - `volume_scalar`: Volume Master atual do Windows (0.0 a 1.0)
    - `peak_meter`: Pico real do sinal digital reproduzido agora (0.0 a 1.0)
    - `is_muted`: Se a saída de áudio está silenciada
    """
    try:
        ole32.CoInitializeEx(None, COINIT_MULTITHREADED)
    except Exception:
        pass

    enumerator = ctypes.c_void_p()
    device = ctypes.c_void_p()
    ep_vol = ctypes.c_void_p()
    meter = ctypes.c_void_p()

    vol_scalar = 0.5
    peak_val = 0.0
    muted = False

    try:
        hr = ole32.CoCreateInstance(
            ctypes.byref(CLSID_MMDeviceEnumerator),
            None,
            CLSCTX_ALL,
            ctypes.byref(IID_IMMDeviceEnumerator),
            ctypes.byref(enumerator),
        )
        if hr != 0 or not enumerator.value:
            return (vol_scalar, peak_val, muted)

        # IMMDeviceEnumerator::GetDefaultAudioEndpoint (vtable slot 4)
        enum_vt = ctypes.cast(enumerator, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
        get_default_ep = ctypes.WINFUNCTYPE(
            ctypes.c_long,
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_uint,
            ctypes.POINTER(ctypes.c_void_p),
        )(enum_vt[4])

        hr = get_default_ep(enumerator, E_RENDER, E_MULTIMEDIA, ctypes.byref(device))
        if hr != 0 or not device.value:
            return (vol_scalar, peak_val, muted)

        # IMMDevice::Activate (vtable slot 3)
        dev_vt = ctypes.cast(device, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
        activate_fn = ctypes.WINFUNCTYPE(
            ctypes.c_long,
            ctypes.c_void_p,
            ctypes.POINTER(GUID),
            ctypes.wintypes.DWORD,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p),
        )(dev_vt[3])

        # 1. IAudioEndpointVolume -> GetMasterVolumeLevelScalar (slot 9) & GetMute (slot 15)
        hr = activate_fn(device, ctypes.byref(IID_IAudioEndpointVolume), CLSCTX_ALL, None, ctypes.byref(ep_vol))
        if hr == 0 and ep_vol.value:
            vol_vt = ctypes.cast(ep_vol, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
            get_vol_scalar = ctypes.WINFUNCTYPE(
                ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(ctypes.c_float)
            )(vol_vt[9])
            get_mute = ctypes.WINFUNCTYPE(
                ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(ctypes.wintypes.BOOL)
            )(vol_vt[15])

            f_vol = ctypes.c_float(0.5)
            b_mute = ctypes.wintypes.BOOL(0)
            if get_vol_scalar(ep_vol, ctypes.byref(f_vol)) == 0:
                vol_scalar = max(0.0, min(1.0, float(f_vol.value)))
            if get_mute(ep_vol, ctypes.byref(b_mute)) == 0:
                muted = bool(b_mute.value)

        # 2. IAudioMeterInformation -> GetPeakValue (slot 3)
        hr = activate_fn(device, ctypes.byref(IID_IAudioMeterInformation), CLSCTX_ALL, None, ctypes.byref(meter))
        if hr == 0 and meter.value:
            meter_vt = ctypes.cast(meter, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
            get_peak = ctypes.WINFUNCTYPE(
                ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(ctypes.c_float)
            )(meter_vt[3])
            f_peak = ctypes.c_float(0.0)
            if get_peak(meter, ctypes.byref(f_peak)) == 0:
                peak_val = max(0.0, min(1.0, float(f_peak.value)))

    except Exception:
        pass
    finally:
        _com_release(meter)
        _com_release(ep_vol)
        _com_release(device)
        _com_release(enumerator)

    return (vol_scalar, peak_val, muted)


class HearingSafetyMonitor:
    """
    Calcula exposição sonora em dB SPL estimados e acumula a dose auditiva segura OMS / Apple iOS
    (referência: 80 dB SPL = 8 horas/dia seguras; taxa de dobra de energia a cada +3 dB).
    """

    # Sensibilidade acústica média de referência para IEMs/TWS modernos (Sony WF-1000XM3 ~ 102 dB SPL @ 0 dBFS RMS)
    REF_MAX_SPL_DB: float = 102.0
    SAFE_DAILY_SECONDS_AT_80DB: float = 8.0 * 3600.0

    def __init__(self) -> None:
        self._last_sample_ts: float = time.monotonic()
        self._smoothed_spl: float = 34.0
        self._daily_dose_pct: float = 0.0
        self._high_spl_streak_sec: float = 0.0
        self._alert_emitted: bool = False

    def sample(self, clear_bass: int = 0, eq_bands: Optional[List[int]] = None) -> Dict[str, Any]:
        """Executa leitura pontual CoreAudio e atualiza o dosímetro psicoacústico."""
        now = time.monotonic()
        dt = min(15.0, max(0.05, now - self._last_sample_ts))
        self._last_sample_ts = now

        vol_scalar, peak_val, is_muted = read_windows_coreaudio_levels()

        # Ganho adicional médio introduzido por reforço positivo de Clear Bass / Equalizador
        bands = eq_bands or [0, 0, 0, 0, 0]
        pos_boosts = [max(0, clear_bass)] + [max(0, b) for b in bands]
        eq_boost_db = (sum(pos_boosts) / len(pos_boosts)) * 0.55

        if is_muted or vol_scalar <= 0.002 or peak_val <= 0.0015:
            instant_spl = 32.0  # Piso silencioso interno com isolamento passivo/ANC
            is_playing = False
        else:
            # Converte volume do Windows + RMS estimado (pico - 5 dB de fator de crista musical típico)
            vol_att_db = 20.0 * math.log10(max(0.001, vol_scalar))
            sig_rms_db = 20.0 * math.log10(max(0.001, peak_val)) - 5.0
            instant_spl = max(34.0, min(110.0, self.REF_MAX_SPL_DB + vol_att_db + sig_rms_db + eq_boost_db))
            is_playing = True

        # Filtro exponencial suave (evita números piscando freneticamente na interface)
        alpha = 0.42 if instant_spl > self._smoothed_spl else 0.24
        self._smoothed_spl = (alpha * instant_spl) + ((1.0 - alpha) * self._smoothed_spl)
        disp_spl = round(self._smoothed_spl, 1)

        # Acumulação de dose diária OMS / ITU-T H.870 (acima de 75 dB SPL)
        should_warn = False
        if is_playing and disp_spl >= 75.0:
            # Fator de intensidade acústica com taxa de troca de 3 dB: I_factor = 2^((SPL - 80)/3)
            intensity_factor = 2.0 ** ((disp_spl - 80.0) / 3.0)
            dose_delta = (dt * intensity_factor / self.SAFE_DAILY_SECONDS_AT_80DB) * 100.0
            self._daily_dose_pct = min(999.0, self._daily_dose_pct + dose_delta)

        if is_playing and disp_spl >= 85.0:
            self._high_spl_streak_sec += dt
            if self._high_spl_streak_sec >= 120.0 and not self._alert_emitted:
                self._alert_emitted = True
                should_warn = True
        else:
            self._high_spl_streak_sec = max(0.0, self._high_spl_streak_sec - dt * 0.5)
            if disp_spl < 80.0:
                self._alert_emitted = False

        if not is_playing:
            zone = "silent"
            label = "Silêncio"
        elif disp_spl < 80.0:
            zone = "safe"
            label = "Seguro (OMS)"
        elif disp_spl < 85.0:
            zone = "moderate"
            label = "Moderado"
        else:
            zone = "loud"
            label = "Volume Alto (>85 dB)"

        return {
            "spl_db": disp_spl,
            "windows_vol_pct": round(vol_scalar * 100),
            "peak_pct": round(peak_val * 100),
            "is_muted": is_muted,
            "is_playing": is_playing,
            "zone": zone,
            "status_label": label,
            "daily_dose_pct": round(self._daily_dose_pct, 2),
            "trigger_warning": should_warn,
        }
