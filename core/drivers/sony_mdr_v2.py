"""
Driver Sony MDR Tandem V2 (WF-1000XM4, WF-1000XM5, WH-1000XM5, LinkBuds S, ULT WEAR) — HeadsetPlus Studio
Autor: Matheus Veras
Licença: Source-Available Proprietary (Ver LICENSE.md)

Estende o transporte RFCOMM resiliente Sony MDR com suporte aos opcodes Tandem V2
(Command Table 1 `data_type=12` e Table 2 `data_type=28`), decodificação de bateria V2
(`0x22`/`0x23`/`0x25` Dual L/R & Charging Case) e sincronização com Windows APO DSP.
"""

import time
from typing import Any, List

from core.drivers.sony_mdr_v1 import SonyMdrV1Driver
from core.mock_driver import MockRfcommSocket, VirtualSonyHeadsetState


class SonyMdrV2Driver(SonyMdrV1Driver):
    """Driver para geração moderna Sony (processadores V1/V2/QN2e — protocolo Tandem V2)."""

    PROTOCOL_ID: str = "sony_mdr_v2"

    def _create_mock_socket(self) -> Any:
        vstate = VirtualSonyHeadsetState()
        clean_base = self.model_name.replace("(Mock)", "").strip() or "WF-1000XM5"
        vstate.model = clean_base
        vstate.fw_version = "4.0.2"
        vstate.codec_id = 0x03  # LDAC Hi-Res
        vstate.bat_l = 96
        vstate.bat_r = 95
        vstate.bat_case = 0 if clean_base.upper().startswith("WH-") else 91
        return MockRfcommSocket(virtual_state=vstate)

    def query_all_states(self) -> None:
        """Executa handshake Tandem V2 seguido de varredura híbrida V2/V1 de telemetria."""
        if not self.connected:
            return
        pause_sec = 0.005 if self.mock_mode else 0.035

        # Handshake inicial Tandem V2 (CONNECT_GET_PROTOCOL_INFO)
        if not self.mock_mode:
            self.send_command(bytes([0x00, 0x00]), wait_ack=True, data_type=12)
            time.sleep(pause_sec)
            # Inquirições de bateria Tandem V2 (0x09 = L/R Dual, 0x0A = Cradle/Case)
            self.send_command(bytes([0x22, 0x09]), wait_ack=True, data_type=12)
            time.sleep(pause_sec)
            self.send_command(bytes([0x22, 0x0A]), wait_ack=True, data_type=12)
            time.sleep(pause_sec)

        # Varredura completa compatível com Table 1 / Mock
        super().query_all_states()

    def _handle_payload(self, pld: bytes, dtype: int = 12) -> None:
        if not pld:
            return
        cmd = pld[0]

        # Tandem V2 Battery Return (0x23) / Notify (0x25)
        if cmd in (0x23, 0x25) and len(pld) >= 4:
            inq = pld[1]
            # Single headset battery (WH-1000XM5 / ULT WEAR)
            if inq in (0x00, 0x08) and len(pld) >= 4:
                pct = min(100, max(0, pld[2]))
                chg = pld[3] == 1
                self.state["bat_l"] = pct
                self.state["bat_r"] = pct
                self.state["bat_l_charging"] = chg
                self.state["bat_r_charging"] = chg
                self.notify_state()
                return
            # Dual L/R TWS battery (WF-1000XM4 / WF-1000XM5 / LinkBuds S)
            if inq in (0x01, 0x09) and len(pld) >= 6:
                self.state["bat_l"] = min(100, max(0, pld[2]))
                self.state["bat_l_charging"] = pld[3] == 1
                self.state["bat_r"] = min(100, max(0, pld[4]))
                self.state["bat_r_charging"] = pld[5] == 1
                self.notify_state()
                return
            # Charging Case battery
            if inq in (0x02, 0x0A) and len(pld) >= 4:
                self.state["bat_case"] = min(100, max(0, pld[2]))
                self.state["bat_case_charging"] = pld[3] == 1
                self.notify_state()
                return

        super()._handle_payload(pld, dtype)

    def set_eq_custom(self, preset_name: str, clear_bass: int, bands: List[int]) -> None:
        super().set_eq_custom(preset_name, clear_bass, bands)
        # Espelha comando na Table 2 (data_type=28) caso conectado em hardware físico Tandem V2
        if self.connected and not self.mock_mode:
            cb_byte = max(0, min(20, int(clear_bass) + 10))
            band_bytes = [max(0, min(20, int(b) + 10)) for b in list(bands)[:5]]
            pld = bytes([0x58, 0x01, 0xA0, 0x06, cb_byte] + band_bytes)
            self.send_command(pld, wait_ack=False, data_type=28)
