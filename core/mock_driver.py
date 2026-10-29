"""
Simulador Virtual de Hardware Bluetooth RFCOMM (Mock Harness) — Sony Sound Connect PC
Autor: Matheus Veras
Licença: Source-Available Proprietary (Ver LICENSE.md)

Emula em nível binário o protocolo proprietário Sony MDR V1 (quadros 0x3E..0x3C,
escape 0x3D, checksum de 8 bits, ACKs de sequência alternada e telemetria assíncrona),
permitindo desenvolvimento, auditoria de UI e testes automatizados sem hardware físico.
"""

import queue
import socket
import struct
import threading
from typing import Callable, Dict, List, Optional, Tuple


# Tabelas de curvas padrão de fábrica para simulação realista de presets de hardware
MOCK_PRESET_CURVES: Dict[int, Tuple[int, List[int]]] = {
    0x00: (0, [0, 0, 0, 0, 0]),       # Desligado (Off)
    0x10: (1, [-1, 0, 2, 4, 5]),      # Brilhante (Bright)
    0x11: (6, [1, 0, 2, 4, 5]),       # Empolgado (Excited)
    0x12: (1, [1, 0, -1, -2, -3]),    # Suave (Mellow)
    0x13: (0, [1, 1, 0, -1, -2]),     # Relaxado (Relaxed)
    0x14: (-2, [-1, 3, 4, 2, -1]),    # Vocal
    0x15: (-1, [-1, 0, 2, 5, 6]),     # Agudos (Treble)
    0x16: (7, [3, 1, 0, -1, -1]),     # Graves (Bass)
    0x17: (-3, [-2, 3, 5, 2, -2]),    # Fala (Speech)
}


def _escape_mdr(data: bytes) -> bytes:
    """Aplica escape de bytes especiais Sony MDR V1 (0x3C, 0x3D, 0x3E)."""
    out = bytearray()
    for b in data:
        if b == 0x3C:
            out.extend((0x3D, 0x2C))
        elif b == 0x3D:
            out.extend((0x3D, 0x2D))
        elif b == 0x3E:
            out.extend((0x3D, 0x2E))
        else:
            out.append(b)
    return bytes(out)


def _unescape_mdr(data: bytes) -> bytes:
    """Remove escape de bytes especiais Sony MDR V1 com proteção contra truncamento."""
    out = bytearray()
    i = 0
    n = len(data)
    while i < n:
        b = data[i]
        if b == 0x3D and i + 1 < n:
            nxt = data[i + 1]
            if nxt == 0x2C:
                out.append(0x3C)
            elif nxt == 0x2D:
                out.append(0x3D)
            elif nxt == 0x2E:
                out.append(0x3E)
            else:
                out.append(nxt)
            i += 2
        else:
            out.append(b)
            i += 1
    return bytes(out)


def _pack_mdr_frame(payload: bytes, data_type: int = 12, seq: int = 0) -> bytes:
    """Empacota um quadro completo Sony MDR V1 com cabeçalho e checksum de 8 bits."""
    header_and_payload = struct.pack(">BBI", data_type, seq, len(payload)) + payload
    checksum = sum(header_and_payload) & 0xFF
    return b"\x3E" + _escape_mdr(header_and_payload + bytes([checksum])) + b"\x3C"


class VirtualSonyHeadsetState:
    """Estado interno persistente do fone virtual simulado durante a sessão."""

    def __init__(self) -> None:
        self.model: str = "WF-1000XM3"
        self.fw_version: str = "3.1.2"
        self.codec_id: int = 0x02  # AAC
        self.bat_l: int = 92
        self.bat_l_charging: int = 0
        self.bat_r: int = 90
        self.bat_r_charging: int = 0
        self.bat_case: int = 85
        self.bat_case_charging: int = 1

        # Cancelamento de Ruído / Som Ambiente (ANC padrão)
        self.nc_effect: int = 0x01
        self.nc_val: int = 0x00
        self.asm_id: int = 0x00
        self.asm_val: int = 9  # Nível 10 (0-indexed = 9)

        # Equalizador DSP (Clear Bass +3, curva Harman inicial)
        self.eq_preset_id: int = 0xA0
        self.clear_bass_raw: int = 13  # +3 dB
        self.eq_bands_raw: List[int] = [9, 12, 14, 13, 12]  # [-1, +2, +4, +3, +2] dB

        # Preferências de hardware
        self.conn_mode: int = 0x01  # Prioridade na Conexão Estável
        self.dsee_hx: int = 0x00
        self.wearing_pause: int = 0x01
        self.auto_off: int = 0x11  # Não desligar
        self.touch_l: int = 0x00   # Controle de Som Ambiente
        self.touch_r: int = 0x20   # Controle de Reprodução


# Instância compartilhada na sessão para preservar ajustes entre reconexões mock
_SHARED_VIRTUAL_STATE = VirtualSonyHeadsetState()


class MockRfcommSocket:
    """
    Substituto drop-in de `socket.socket(AF_BLUETOOTH, SOCK_STREAM, BTPROTO_RFCOMM)`.
    Processa quadros binários Sony MDR V1 em memória com consumo 0.0% de CPU em standby.
    """

    def __init__(
        self,
        virtual_state: Optional[VirtualSonyHeadsetState] = None,
        enable_battery_ticker: bool = True,
    ) -> None:
        self._state: VirtualSonyHeadsetState = virtual_state or _SHARED_VIRTUAL_STATE
        self._rx_queue: "queue.Queue[bytes]" = queue.Queue()
        self._tx_buf: bytearray = bytearray()
        self._timeout: Optional[float] = 4.5
        self._closed: bool = False
        self._tx_seq: int = 0
        self._lock: threading.Lock = threading.Lock()
        self._stop_event: threading.Event = threading.Event()
        self._ticker_thread: Optional[threading.Thread] = None
        self._enable_battery_ticker: bool = enable_battery_ticker

    def settimeout(self, value: Optional[float]) -> None:
        """Define o timeout de leitura compatível com WinSock."""
        self._timeout = value

    def connect(self, address: Tuple[str, int]) -> None:
        """Simula o handshake RFCOMM com o dispositivo virtual."""
        if self._closed:
            raise OSError("Socket mock já foi encerrado.")
        if self._enable_battery_ticker:
            self._ticker_thread = threading.Thread(
                target=self._battery_telemetry_worker,
                name="SonyMockBatteryTicker",
                daemon=True,
            )
            self._ticker_thread.start()

    def send(self, data: bytes) -> int:
        """Recebe bytes enviados pelo cliente Python, valida quadros e enfileira respostas."""
        if self._closed:
            raise OSError("Conexão RFCOMM virtual fechada.")
        with self._lock:
            self._tx_buf.extend(data)
            self._process_incoming_stream()
        return len(data)

    def recv(self, bufsize: int = 1024) -> bytes:
        """Entrega quadros de resposta do fone virtual respeitando o timeout configurado."""
        if self._closed:
            return b""
        try:
            pkt = self._rx_queue.get(timeout=self._timeout)
            if pkt == b"":
                return b""
            if len(pkt) > bufsize:
                # Re-enfileira excedente caso bufsize seja pequeno (teste de fragmentação)
                head, tail = pkt[:bufsize], pkt[bufsize:]
                with self._rx_queue.mutex:
                    self._rx_queue.queue.appendleft(tail)
                return head
            return pkt
        except queue.Empty:
            raise socket.timeout("timed out")

    def close(self) -> None:
        """Encerra o socket virtual e libera imediatamente qualquer thread bloqueada em recv()."""
        if not self._closed:
            self._closed = True
            self._stop_event.set()
            self._rx_queue.put(b"")

    # ================= PROCESSAMENTO INTERNO DO PROTOCOLO SONY MDR V1 =================

    def _enqueue_frame(self, payload: bytes, data_type: int = 12, seq: Optional[int] = None) -> None:
        if self._closed:
            return
        if seq is None:
            seq = self._tx_seq
            self._tx_seq = 1 - self._tx_seq
        frame = _pack_mdr_frame(payload, data_type=data_type, seq=seq)
        self._rx_queue.put(frame)

    def _process_incoming_stream(self) -> None:
        while True:
            start = self._tx_buf.find(b"\x3E")
            if start == -1:
                self._tx_buf.clear()
                return
            if start > 0:
                del self._tx_buf[:start]

            end = self._tx_buf.find(b"\x3C", 1)
            if end == -1:
                return

            raw_frame = bytes(self._tx_buf[1:end])
            del self._tx_buf[: end + 1]

            un = _unescape_mdr(raw_frame)
            if len(un) < 7:
                continue

            dtype = un[0]
            rseq = un[1]
            plen = struct.unpack(">I", un[2:6])[0]
            if len(un) != 6 + plen + 1:
                continue

            expected_chk = sum(un[: 6 + plen]) & 0xFF
            if un[6 + plen] != expected_chk:
                continue

            if dtype == 1:
                # ACK recebido do host -> nenhuma ação necessária
                continue

            if dtype in (12, 13, 14):
                # Envia ACK imediato com sequência invertida conforme especificação MDR
                ack_seq = 1 - rseq if rseq in (0, 1) else 0
                self._enqueue_frame(b"", data_type=1, seq=ack_seq)
                payload = un[6 : 6 + plen]
                self._handle_host_command(payload)

    def _handle_host_command(self, pld: bytes) -> None:
        if not pld:
            return
        st = self._state
        cmd = pld[0]

        # 0x04: Consulta de Modelo / Firmware
        if cmd == 0x04 and len(pld) >= 2:
            info_type = pld[1]
            text = st.model if info_type == 0x01 else st.fw_version
            raw_str = text.encode("utf-8")
            self._enqueue_frame(bytes([0x05, info_type, len(raw_str)]) + raw_str)

        # 0x10: Consulta de Bateria (0x01 = L/R, 0x02 = Case)
        elif cmd == 0x10 and len(pld) >= 2:
            bat_type = pld[1]
            if bat_type == 0x01:
                self._enqueue_frame(
                    bytes([0x11, 0x01, st.bat_l, st.bat_l_charging, st.bat_r, st.bat_r_charging])
                )
            elif bat_type == 0x02:
                self._enqueue_frame(bytes([0x11, 0x02, st.bat_case, st.bat_case_charging]))

        # 0x18: Consulta de Codec Bluetooth Ativo
        elif cmd == 0x18:
            self._enqueue_frame(bytes([0x19, 0x00, st.codec_id]))

        # 0x56: Consulta do Equalizador DSP
        elif cmd == 0x56 and len(pld) >= 2:
            self._enqueue_frame(
                bytes([0x57, 0x01, st.eq_preset_id, 0x06, st.clear_bass_raw] + st.eq_bands_raw)
            )

        # 0x58: Escrita do Equalizador DSP (Custom ou Preset)
        elif cmd == 0x58 and len(pld) >= 4:
            if pld[1] == 0x01:
                st.eq_preset_id = pld[2]
                count = pld[3]
                if count >= 6 and len(pld) >= 4 + count:
                    st.clear_bass_raw = max(0, min(20, pld[4]))
                    st.eq_bands_raw = [max(0, min(20, pld[5 + i])) for i in range(5)]
                elif st.eq_preset_id in MOCK_PRESET_CURVES:
                    cb, bands = MOCK_PRESET_CURVES[st.eq_preset_id]
                    st.clear_bass_raw = cb + 10
                    st.eq_bands_raw = [b + 10 for b in bands]
                self._enqueue_frame(
                    bytes([0x59, 0x01, st.eq_preset_id, 0x06, st.clear_bass_raw] + st.eq_bands_raw)
                )

        # 0x66: Consulta de Cancelamento de Ruído / Som Ambiente
        elif cmd == 0x66 and len(pld) >= 2:
            self._enqueue_frame(
                bytes([0x67, 0x02, st.nc_effect, 0x00, st.nc_val, 0x01, st.asm_id, st.asm_val])
            )

        # 0x68: Alteração de Cancelamento de Ruído / Som Ambiente
        elif cmd == 0x68 and len(pld) >= 8:
            if pld[1] == 0x02:
                st.nc_effect = pld[2]
                st.nc_val = pld[4]
                st.asm_id = pld[6]
                st.asm_val = max(0, min(19, pld[7]))
                self._enqueue_frame(
                    bytes([0x69, 0x02, st.nc_effect, 0x00, st.nc_val, 0x01, st.asm_id, st.asm_val])
                )

        # 0xF6: Consulta de Recursos de Sistema e Sensores
        elif cmd == 0xF6 and len(pld) >= 2:
            feat = pld[1]
            if feat == 0x01:
                self._enqueue_frame(bytes([0xF7, 0x01, st.conn_mode]))
            elif feat == 0x02:
                self._enqueue_frame(bytes([0xF7, 0x02, st.dsee_hx]))
            elif feat == 0x03:
                self._enqueue_frame(bytes([0xF7, 0x03, st.wearing_pause]))
            elif feat == 0x04:
                self._enqueue_frame(bytes([0xF7, 0x04, st.auto_off]))
            elif feat == 0x06:
                self._enqueue_frame(bytes([0xF7, 0x06, st.touch_l, st.touch_r]))

        # 0xF8: Escrita de Recursos de Sistema e Sensores
        elif cmd == 0xF8 and len(pld) >= 4:
            feat = pld[1]
            if feat == 0x01:
                st.conn_mode = pld[3]
                # Se mudar prioridade de qualidade, alterna codec simulado entre AAC e SBC/LDAC
                st.codec_id = 0x02 if st.conn_mode == 0x01 else 0x03
                self._enqueue_frame(bytes([0x1B, 0x00, st.codec_id]))
            elif feat == 0x02:
                st.dsee_hx = pld[3]
            elif feat == 0x03:
                st.wearing_pause = pld[3]
            elif feat == 0x04:
                st.auto_off = pld[3]
            elif feat == 0x06 and len(pld) >= 5:
                st.touch_l = pld[3]
                st.touch_r = pld[4]

        # 0x22: Desligamento Remoto dos Fones
        elif cmd == 0x22:
            self.close()

    def _battery_telemetry_worker(self) -> None:
        """
        Emite notificações realistas de telemetria de bateria a cada 25s
        usando `Event.wait()` (0.0% de uso de CPU entre pulsos).
        """
        while not self._stop_event.wait(timeout=25.0):
            if self._closed:
                break
            st = self._state
            # Simula descarga gradual dos fones em uso e recarga suave do estojo
            if st.bat_l > 15:
                st.bat_l -= 1
            else:
                st.bat_l = 95
            if st.bat_r > 14:
                st.bat_r -= 1
            else:
                st.bat_r = 94

            if st.bat_case_charging:
                st.bat_case = min(100, st.bat_case + 1)
                if st.bat_case >= 100:
                    st.bat_case_charging = 0

            self._enqueue_frame(
                bytes([0x13, 0x01, st.bat_l, st.bat_l_charging, st.bat_r, st.bat_r_charging])
            )
            self._enqueue_frame(bytes([0x13, 0x02, st.bat_case, st.bat_case_charging]))

