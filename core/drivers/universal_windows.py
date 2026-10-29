"""
Driver Universal Windows 11 (Bateria Bluetooth PnP + Motor Global Equalizer APO) — Sony Sound Connect PC
Autor: Matheus Veras
Licença: Source-Available Proprietary (Ver LICENSE.md)

Suporta qualquer fone Bluetooth pareado no Windows 11 (ex: realme Buds Air 5 Pro, Apple AirPods Pro,
Samsung Galaxy Buds, Bose QuietComfort, Sennheiser Momentum, JBL):
- Lê a porcentagem real de bateria reportada via HFP/BLE ao Windows 11 (`DEVPKEY_Bluetooth_Battery`)
- Processa Equalizador Paramétrico de 6 bandas, Clear Bass, AutoEq, Perfis Biométricos ISO 226 e
  Crossfeed 3D Linkwitz/Chu-Moy globalmente em nível de sistema via `WindowsApoEngine`
"""

import threading
from typing import Any, Callable, List, Optional

from core.device_detector import query_windows_bluetooth_battery
from core.drivers.base import BaseHeadsetDriver
from core.mock_driver import MOCK_PRESET_CURVES
from core.drivers.base import EQ_PRESETS


class UniversalWindowsDriver(BaseHeadsetDriver):
    """Driver universal multimarca alimentado por telemetria PnP Windows 11 e DSP Global APO."""

    PROTOCOL_ID: str = "universal_windows"

    def __init__(
        self,
        mac: str = "",
        port: int = 0,
        model_name: str = "realme Buds Air 5 Pro",
        brand_name: str = "realme",
        mock_mode: bool = False,
        apo_engine: Optional[Any] = None,
        on_state_update: Optional[Callable[[], None]] = None,
        on_status_msg: Optional[Callable[[str], None]] = None,
        on_wearing_event: Optional[Callable[[bool], None]] = None,
    ) -> None:
        super().__init__(
            mac=mac,
            port=port,
            model_name=model_name,
            brand_name=brand_name,
            mock_mode=mock_mode,
            apo_engine=apo_engine,
            on_state_update=on_state_update,
            on_status_msg=on_status_msg,
            on_wearing_event=on_wearing_event,
        )
        self._poll_stop = threading.Event()
        self._poll_thread: Optional[threading.Thread] = None
        self.state["codec"] = "A2DP + Windows APO"
        self.state["fw_version"] = "Win11 APO Bridge"
        self.state["nc_mode"] = "Hardware Nativo"

    def connect(
        self,
        mac: Optional[str] = None,
        port: Optional[int] = None,
        is_auto_retry: bool = False,
    ) -> bool:
        if mac is not None:
            self.mac = mac
            self.state["mac"] = mac

        self._poll_stop.set()
        self._manual_disconnect = False
        self.state["mock_mode"] = self.mock_mode
        self.state["model"] = self.model_name
        self.state["brand"] = self.brand_name
        self.state["codec"] = "A2DP + Windows APO"

        # Verificação Win32 instantânea de conexão real no Bluetooth do Windows
        if not self.mock_mode:
            from core.device_detector import is_windows_bluetooth_connected
            if not is_windows_bluetooth_connected(self.mac, self.model_name):
                self.connected = False
                self.state["connected"] = False
                self.state["bat_l"] = 0
                self.state["bat_r"] = 0
                self.state["bat_case"] = 0
                self.log(f"Dispositivo {self.model_name} desconectado no Bluetooth do Windows.")
                self.notify_state()
                return False

        self.log(f"Ativando Ponte Universal Windows 11 & DSP Global para {self.model_name}...")
        bat_pct = self._refresh_battery_once()

        self.connected = True
        self.state["connected"] = True
        self._sync_apo_eq(
            str(self.state.get("eq_preset", "Manual (Custom)")),
            int(self.state.get("clear_bass", 0)),
            list(self.state.get("eq_bands", [0, 0, 0, 0, 0])),
        )

        self._poll_stop = threading.Event()
        self._poll_thread = threading.Thread(
            target=self._battery_watch_loop,
            name="UniversalPnpBatteryWatch",
            daemon=True,
        )
        self._poll_thread.start()

        bat_desc = f"Bateria PnP: {bat_pct}%" if bat_pct > 0 else "DSP Global APO Ativo"
        self.log(f"✅ {self.model_name} conectado via Motor Universal Windows 11 ({bat_desc})!")
        self.notify_state()
        return True

    def _refresh_battery_once(self) -> int:
        if self.mock_mode:
            pct = 88
        else:
            queried = query_windows_bluetooth_battery(self.mac, self.model_name)
            pct = int(queried) if queried is not None else 0

        self.state["bat_l"] = pct
        self.state["bat_r"] = pct
        self.state["bat_case"] = 0
        self.state["bat_l_charging"] = False
        self.state["bat_r_charging"] = False
        self.state["bat_case_charging"] = False
        return pct

    def _battery_watch_loop(self) -> None:
        """Atualiza bateria PnP a cada 45s dormindo em Event.wait (0.00% CPU em standby)."""
        stop_ev = self._poll_stop
        while not stop_ev.wait(timeout=45.0):
            if self._shutdown_flag or self._manual_disconnect or not self.connected:
                break
            prev = self.state.get("bat_l", 0)
            curr = self._refresh_battery_once()
            if curr != prev:
                self.notify_state()

    def disconnect(self) -> None:
        self._manual_disconnect = True
        self._poll_stop.set()
        self.connected = False
        self.state["connected"] = False

    def set_eq_custom(self, preset_name: str, clear_bass: int, bands: List[int]) -> None:
        super().set_eq_custom(preset_name, clear_bass, bands)
        self.log(f"🎛️ DSP Global Windows APO atualizado para {self.model_name}: {preset_name}")

    def set_eq_preset_only(self, preset_name: str) -> None:
        preset_id = EQ_PRESETS.get(preset_name, 0x00)
        cb, bds = MOCK_PRESET_CURVES.get(preset_id, (0, [0, 0, 0, 0, 0]))
        self.set_eq_custom(preset_name, cb, list(bds))
