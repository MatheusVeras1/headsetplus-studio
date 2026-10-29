"""
Interface Base de Drivers Multimarca (Plugin Architecture) — Sony Sound Connect PC
Autor: Matheus Veras
Licença: Source-Available Proprietary (Ver LICENSE.md)

Define o contrato unificado e a fila de comandos coalescente (0 thread-storms) compartilhada por:
- `SonyMdrV1Driver` (WF-1000XM3, WH-1000XM3, WH-1000XM4)
- `SonyMdrV2Driver` (WF-1000XM4, WF-1000XM5, WH-1000XM5, LinkBuds S, ULT WEAR)
- `UniversalWindowsDriver` (realme Buds Air 5 Pro, AirPods, Galaxy Buds, Bose, Sennheiser + Windows APO DSP)
"""

import threading
from typing import Any, Callable, Dict, List, Optional, Tuple

EQ_PRESETS: Dict[str, int] = {
    "Desligado (Off)": 0x00,
    "Brilhante (Bright)": 0x10,
    "Empolgado (Excited)": 0x11,
    "Suave (Mellow)": 0x12,
    "Relaxado (Relaxed)": 0x13,
    "Vocal": 0x14,
    "Agudos (Treble)": 0x15,
    "Graves (Bass)": 0x16,
    "Fala (Speech)": 0x17,
    "Rock": 0x01,
    "Pop": 0x02,
    "Jazz": 0x03,
    "Dance": 0x04,
    "EDM": 0x05,
    "R&B / Hip-Hop": 0x06,
    "Acústico": 0x07,
    "Manual (Custom)": 0xA0,
    "Personalizado 1": 0xA1,
    "Personalizado 2": 0xA2,
}
EQ_ID_TO_NAME: Dict[int, str] = {v: k for k, v in EQ_PRESETS.items()}

AUTO_OFF_OPTIONS: Dict[str, int] = {
    "Ao retirar dos ouvidos": 0x10,
    "Após 5 minutos": 0x00,
    "Após 30 minutos": 0x01,
    "Após 1 hora": 0x02,
    "Após 3 horas": 0x03,
    "Não desligar": 0x11,
}
AUTO_OFF_ID_TO_NAME: Dict[int, str] = {v: k for k, v in AUTO_OFF_OPTIONS.items()}

TOUCH_OPTIONS: Dict[str, int] = {
    "Controle de Som Ambiente": 0x00,
    "Controle de Volume": 0x10,
    "Controle de Reprodução": 0x20,
    "Assistente de Voz": 0x30,
    "Google Assistant": 0x31,
    "Amazon Alexa": 0x32,
    "Nenhuma Função": 0xFF,
}
TOUCH_ID_TO_NAME: Dict[int, str] = {v: k for k, v in TOUCH_OPTIONS.items()}


class BaseHeadsetDriver:
    """Classe base para provedores de hardware Bluetooth e DSP Global do Windows 11."""

    PROTOCOL_ID: str = "base"

    def __init__(
        self,
        mac: str = "",
        port: int = 9,
        model_name: str = "WF-1000XM3",
        brand_name: str = "Sony",
        mock_mode: bool = False,
        apo_engine: Optional[Any] = None,
        on_state_update: Optional[Callable[[], None]] = None,
        on_status_msg: Optional[Callable[[str], None]] = None,
        on_wearing_event: Optional[Callable[[bool], None]] = None,
    ) -> None:
        self.mac: str = mac
        self.port: int = port
        self.model_name: str = model_name
        self.brand_name: str = brand_name
        self.mock_mode: bool = mock_mode
        self.apo_engine: Optional[Any] = apo_engine
        self.connected: bool = False

        self.on_state_update = on_state_update
        self.on_status_msg = on_status_msg
        self.on_wearing_event = on_wearing_event

        self._manual_disconnect: bool = False
        self._system_suspended: bool = False
        self._shutdown_flag: bool = False

        # Fila coalescente de comandos (evita proliferação de threads ao arrastar sliders)
        self._cmd_cond: threading.Condition = threading.Condition()
        self._pending_cmds: Dict[str, Tuple[Callable[..., Any], Tuple[Any, ...]]] = {}
        self._cmd_order: List[str] = []
        self._cmd_worker: threading.Thread = threading.Thread(
            target=self._command_worker_loop,
            name=f"HeadsetCmdWorker_{self.PROTOCOL_ID}",
            daemon=True,
        )
        self._cmd_worker.start()

        self.state: Dict[str, Any] = {
            "protocol": self.PROTOCOL_ID,
            "brand": self.brand_name,
            "connected": False,
            "mock_mode": self.mock_mode,
            "mac": self.mac,
            "model": self.model_name,
            "fw_version": "3.1.2",
            "bat_l": 0,
            "bat_l_charging": False,
            "bat_r": 0,
            "bat_r_charging": False,
            "bat_case": 0,
            "bat_case_charging": False,
            "codec": "AAC",
            "nc_mode": "ANC",
            "asm_level": 10,
            "focus_on_voice": False,
            "eq_preset": "Manual (Custom)",
            "clear_bass": 0,
            "eq_bands": [0, 0, 0, 0, 0],
            "dsee_hx": False,
            "wearing_pause": False,
            "in_ear_detected": None,
            "auto_off": "Não desligar",
            "conn_mode": "Prioridade na Conexão Estável",
            "touch_l": "Controle de Som Ambiente",
            "touch_r": "Controle de Reprodução",
            "apo_global_active": bool(self.apo_engine and self.apo_engine.enabled),
        }

    def log(self, msg: str) -> None:
        if self.on_status_msg:
            self.on_status_msg(msg)

    def notify_state(self) -> None:
        if self.apo_engine is not None:
            self.state["apo_global_active"] = bool(self.apo_engine.enabled)
        if self.on_state_update:
            self.on_state_update()

    def _sync_apo_eq(self, label: str, clear_bass: int, bands: List[int]) -> None:
        if self.apo_engine is not None:
            try:
                self.apo_engine.update_eq(label, clear_bass, bands)
            except Exception:
                pass

    def enqueue_action(self, category_key: str, fn: Callable[..., Any], *args: Any) -> None:
        """Enfileira comandos coalescendo eventos rápidos da mesma categoria."""
        with self._cmd_cond:
            if category_key not in self._pending_cmds:
                self._cmd_order.append(category_key)
            self._pending_cmds[category_key] = (fn, args)
            self._cmd_cond.notify()

    def _command_worker_loop(self) -> None:
        while not self._shutdown_flag:
            with self._cmd_cond:
                while not self._cmd_order and not self._shutdown_flag:
                    self._cmd_cond.wait()
                if self._shutdown_flag:
                    return
                key = self._cmd_order.pop(0)
                fn, args = self._pending_cmds.pop(key)
            try:
                fn(*args)
            except Exception:
                pass

    def set_mock_mode(self, enabled: bool) -> bool:
        self.mock_mode = bool(enabled)
        self.state["mock_mode"] = self.mock_mode
        return self.connect()

    def connect(
        self,
        mac: Optional[str] = None,
        port: Optional[int] = None,
        is_auto_retry: bool = False,
    ) -> bool:
        raise NotImplementedError

    def disconnect(self) -> None:
        self._manual_disconnect = True
        self.connected = False
        self.state["connected"] = False

    def shutdown(self) -> None:
        self._shutdown_flag = True
        self.disconnect()
        with self._cmd_cond:
            self._cmd_cond.notify_all()

    def handle_system_suspend(self) -> None:
        self._system_suspended = True
        self.disconnect()

    def handle_system_resume(self) -> None:
        self._system_suspended = False
        if not self._shutdown_flag:
            self.connect(is_auto_retry=True)

    # Métodos padrão de controle (sobrescritos conforme capacidades de cada protocolo)
    def set_nc_asm(self, mode: str, asm_level: int = 10, focus_voice: bool = False) -> None:
        self.state["nc_mode"] = mode
        self.state["asm_level"] = int(asm_level)
        self.state["focus_on_voice"] = bool(focus_voice)
        self.notify_state()

    def set_eq_custom(self, preset_name: str, clear_bass: int, bands: List[int]) -> None:
        clean_bands = [int(b) for b in list(bands)[:5]]
        while len(clean_bands) < 5:
            clean_bands.append(0)
        self.state["eq_preset"] = preset_name
        self.state["clear_bass"] = int(clear_bass)
        self.state["eq_bands"] = clean_bands
        self._sync_apo_eq(preset_name, int(clear_bass), clean_bands)
        self.notify_state()

    def set_eq_preset_only(self, preset_name: str) -> None:
        self.state["eq_preset"] = preset_name
        self.notify_state()

    def set_connection_mode(self, stable_priority: bool) -> None:
        self.state["conn_mode"] = (
            "Prioridade na Conexão Estável" if stable_priority else "Prioridade na Qualidade do Som"
        )
        self.notify_state()

    def set_dsee_hx(self, enabled: bool) -> None:
        self.state["dsee_hx"] = bool(enabled)
        self.notify_state()

    def set_wearing_pause(self, enabled: bool) -> None:
        self.state["wearing_pause"] = bool(enabled)
        self.notify_state()

    def set_auto_power_off(self, option_name: str) -> None:
        self.state["auto_off"] = option_name
        self.notify_state()

    def set_touch_sensors(self, left_name: str, right_name: str) -> None:
        self.state["touch_l"] = left_name
        self.state["touch_r"] = right_name
        self.notify_state()

    def power_off_headphones(self) -> None:
        self.disconnect()
        self.notify_state()
