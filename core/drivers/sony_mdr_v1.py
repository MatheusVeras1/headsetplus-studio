"""
Driver Sony MDR V1 (WF-1000XM3, WH-1000XM3, WH-1000XM4) — HeadsetPlus Studio
Autor: Matheus Veras
Licença: Source-Available Proprietary (Ver LICENSE.md)

Implementa o protocolo binário Sony Headphones Connect V1 sobre RFCOMM Serial (porta 9) com:
- Recomposição resiliente de pacotes fragmentados, escape 0x3D e checksum 8-bit
- Reconexão Exponential Backoff + Jitter (±18%) e ciclo Sleep/Resume Windows 11
- Sincronização dupla: DSP embarcado no chip QN1e/QN1 + Motor Global Windows APO
"""

import random
import socket
import struct
import threading
import time
from typing import Any, Callable, List, Optional, Tuple

from core.drivers.base import (
    AUTO_OFF_ID_TO_NAME,
    AUTO_OFF_OPTIONS,
    BaseHeadsetDriver,
    EQ_ID_TO_NAME,
    EQ_PRESETS,
    TOUCH_ID_TO_NAME,
    TOUCH_OPTIONS,
)
from core.mock_driver import MockRfcommSocket, MOCK_PRESET_CURVES

MAX_RX_BUFFER_BYTES: int = 16384


def escape_specials(data: bytes) -> bytes:
    """Codifica bytes reservados do framing Sony MDR (0x3C, 0x3D, 0x3E)."""
    res = bytearray()
    for b in data:
        if b == 0x3C:
            res.extend((0x3D, 0x2C))
        elif b == 0x3D:
            res.extend((0x3D, 0x2D))
        elif b == 0x3E:
            res.extend((0x3D, 0x2E))
        else:
            res.append(b)
    return bytes(res)


def unescape_specials(data: bytes) -> bytes:
    """Decodifica sequências de escape 0x3D protegendo contra bytes órfãos ou truncados."""
    res = bytearray()
    i = 0
    n = len(data)
    while i < n:
        b = data[i]
        if b == 0x3D and i + 1 < n:
            nxt = data[i + 1]
            if nxt == 0x2C:
                res.append(0x3C)
            elif nxt == 0x2D:
                res.append(0x3D)
            elif nxt == 0x2E:
                res.append(0x3E)
            else:
                res.append(nxt)
            i += 2
        else:
            res.append(b)
            i += 1
    return bytes(res)


def make_packet(payload: bytes, data_type: int = 12, seq: int = 0) -> bytes:
    """Monta um pacote Sony MDR completo com cabeçalho Big-Endian e checksum de 8 bits."""
    header_and_payload = struct.pack(">BBI", data_type, seq, len(payload)) + payload
    chk = sum(header_and_payload) & 0xFF
    body = header_and_payload + bytes([chk])
    return b"\x3E" + escape_specials(body) + b"\x3C"


def make_ack(seq: int) -> bytes:
    """Gera pacote de confirmação ACK (data_type=1) para a sequência informada."""
    return make_packet(b"", data_type=1, seq=seq)


def extract_mdr_frames(buf: bytes) -> Tuple[List[Tuple[int, int, bytes]], bytes]:
    """
    Recompõe e valida pacotes fragmentados de um stream contínuo RFCOMM Sony MDR.
    - Descarta ruído/bytes órfãos (ex: 0x3C espúrio antes de 0x3E).
    - Recupera-se instantaneamente de quadros parciais abortados (novo 0x3E antes de 0x3C).
    - Valida tamanho exato do payload e integridade do checksum de 8 bits.
    """
    valid_frames: List[Tuple[int, int, bytes]] = []

    while buf:
        start = buf.find(b"\x3E")
        if start == -1:
            return valid_frames, b""
        if start > 0:
            buf = buf[start:]

        end = buf.find(b"\x3C", 1)
        next_start = buf.find(b"\x3E", 1)

        if next_start != -1 and (end == -1 or next_start < end):
            buf = buf[next_start:]
            continue

        if end == -1:
            if len(buf) > MAX_RX_BUFFER_BYTES:
                buf = b""
            break

        raw_frame = buf[1:end]
        buf = buf[end + 1 :]

        un = unescape_specials(raw_frame)
        if len(un) < 7:
            continue

        dtype = un[0]
        rseq = un[1]
        plen = struct.unpack(">I", un[2:6])[0]

        if len(un) != 6 + plen + 1:
            continue

        expected_chk = sum(un[: 6 + plen]) & 0xFF
        actual_chk = un[6 + plen]
        if actual_chk != expected_chk:
            continue

        valid_frames.append((dtype, rseq, un[6 : 6 + plen]))

    return valid_frames, buf


class SonyMdrV1Driver(BaseHeadsetDriver):
    """Cliente RFCOMM resiliente para protocolo Sony MDR V1 (WF-1000XM3 & série 1000X)."""

    PROTOCOL_ID: str = "sony_mdr"

    def __init__(
        self,
        mac: str = "14:3F:A6:5D:DF:D5",
        port: int = 9,
        model_name: str = "WF-1000XM3",
        brand_name: str = "Sony",
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
        self.sock: Optional[Any] = None
        self.seq: int = 0
        self.lock: threading.Lock = threading.Lock()
        self.ack_event: threading.Event = threading.Event()
        self.running: bool = False
        self.rx_thread: Optional[threading.Thread] = None

        self._backoff_cancel_event: threading.Event = threading.Event()
        self._backoff_lock: threading.Lock = threading.Lock()
        self._backoff_active: bool = False

    def set_mock_mode(self, enabled: bool) -> bool:
        self.mock_mode = bool(enabled)
        self.state["mock_mode"] = self.mock_mode
        if not self.mock_mode and str(self.state.get("model", "")).endswith("(Mock)"):
            self.state["model"] = self.model_name
        return self.connect()

    def connect(
        self,
        mac: Optional[str] = None,
        port: Optional[int] = None,
        is_auto_retry: bool = False,
    ) -> bool:
        if mac:
            self.mac = mac
            self.state["mac"] = mac
        if port:
            self.port = port

        if not is_auto_retry:
            self._backoff_cancel_event.set()

        self._close_socket_only()
        self._manual_disconnect = False
        self.state["mock_mode"] = self.mock_mode

        # Verificação Win32 instantânea (<2ms): se o fone não estiver conectado no Bluetooth do Windows,
        # encerra imediatamente sem falso positivo e sem atraso de timeout no socket
        if not self.mock_mode and self.mac:
            from core.device_detector import is_windows_bluetooth_connected
            if not is_windows_bluetooth_connected(self.mac, self.model_name):
                self.connected = False
                self.state["connected"] = False
                self.state["bat_l"] = 0
                self.state["bat_r"] = 0
                self.state["bat_case"] = 0
                self.log(f"Fone {self.model_name} desconectado no Bluetooth do Windows (estojo fechado).")
                self.notify_state()
                return False

        target_desc = "Simulador Virtual Mock" if self.mock_mode else f"{self.mac} • Canal RFCOMM {self.port}"
        self.log(f"Conectando a {self.model_name} ({target_desc})...")

        s: Optional[Any] = None
        try:
            if self.mock_mode:
                s = self._create_mock_socket()
            else:
                s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            s.settimeout(4.5)
            s.connect((self.mac, self.port))
            self.sock = s
            self.connected = True
            self.state["connected"] = True
            self.running = True
            self.seq = 0

            self.rx_thread = threading.Thread(
                target=self._rx_loop,
                name=f"SonyRxLoop_{self.PROTOCOL_ID}",
                daemon=True,
            )
            self.rx_thread.start()

            self.log(f"✅ Conectado a {self.model_name}! Sincronizando telemetria em tempo real...")
            self.notify_state()
            self.query_all_states()
            return True
        except Exception as e:
            if s is not None:
                try:
                    s.close()
                except Exception:
                    pass
            self.sock = None
            self.connected = False
            self.state["connected"] = False
            self.log(f"Fone em standby ou fora do alcance ({e}). Retire do estojo para auto-conexão.")
            self.notify_state()
            return False

    def _create_mock_socket(self) -> Any:
        return MockRfcommSocket()

    def _close_socket_only(self) -> None:
        self.running = False
        self.connected = False
        self.state["connected"] = False
        sock_ref = self.sock
        self.sock = None
        if sock_ref is not None:
            try:
                sock_ref.close()
            except Exception:
                pass

    def disconnect(self) -> None:
        self._manual_disconnect = True
        self._backoff_cancel_event.set()
        self._close_socket_only()

    def handle_system_suspend(self) -> None:
        self._system_suspended = True
        self._backoff_cancel_event.set()
        was_conn = self.connected
        self._close_socket_only()
        if was_conn:
            self.log("💤 Windows 11 em suspensão: link Bluetooth liberado de forma limpa.")
            self.notify_state()

    def handle_system_resume(self) -> None:
        self._system_suspended = False
        if not self._manual_disconnect and not self._shutdown_flag:
            self.log("⚡ Windows 11 retomado: agendando reconexão inteligente Bluetooth...")
            self._schedule_auto_reconnect(initial_delay=2.0)

    def _schedule_auto_reconnect(self, initial_delay: float = 1.5) -> None:
        if self._manual_disconnect or self._system_suspended or self._shutdown_flag:
            return
        with self._backoff_lock:
            if self._backoff_active:
                return
            self._backoff_active = True
            self._backoff_cancel_event.clear()

        def _backoff_supervisor() -> None:
            base_delay = 1.8
            max_delay = 30.0
            max_attempts = 6
            try:
                if initial_delay > 0 and self._backoff_cancel_event.wait(timeout=initial_delay):
                    return
                for attempt in range(max_attempts):
                    if (
                        self.connected
                        or self._manual_disconnect
                        or self._system_suspended
                        or self._shutdown_flag
                    ):
                        return
                    if self.connect(is_auto_retry=True):
                        return
                    raw_wait = min(max_delay, base_delay * (2 ** attempt))
                    jittered_wait = raw_wait * random.uniform(0.82, 1.18)
                    self.log(f"🔄 Reconexão automática ({attempt + 1}/{max_attempts}) em {jittered_wait:.1f}s...")
                    if self._backoff_cancel_event.wait(timeout=jittered_wait):
                        return
            finally:
                with self._backoff_lock:
                    self._backoff_active = False

        threading.Thread(
            target=_backoff_supervisor,
            name="SonyRfcommBackoffSupervisor",
            daemon=True,
        ).start()

    def send_command(self, payload: bytes, wait_ack: bool = True, data_type: int = 12) -> bool:
        if not self.connected or not self.sock:
            return False
        with self.lock:
            sock_ref = self.sock
            if not sock_ref:
                return False
            self.ack_event.clear()
            pkt = make_packet(payload, data_type=data_type, seq=self.seq)
            try:
                sock_ref.send(pkt)
            except Exception as e:
                self.connected = False
                self.state["connected"] = False
                self.log(f"Conexão RFCOMM interrompida: {e}")
                self.notify_state()
                if not self._manual_disconnect and not self._system_suspended:
                    self._schedule_auto_reconnect()
                return False

            if wait_ack:
                got_ack = self.ack_event.wait(timeout=1.5)
                self.seq = 1 - self.seq
                return got_ack
            else:
                self.seq = 1 - self.seq
                return True

    def _rx_loop(self) -> None:
        buf = b""
        unexpected_drop = False
        while self.running and self.sock:
            try:
                chunk = self.sock.recv(1024)
                if not chunk:
                    unexpected_drop = not self._manual_disconnect and not self._system_suspended
                    break
                buf += chunk
                frames, buf = extract_mdr_frames(buf)
                for dtype, rseq, pld in frames:
                    if dtype == 1:
                        self.ack_event.set()
                    elif dtype in (12, 13, 14, 28, 29, 30):
                        ack_seq = 1 - rseq if rseq in (0, 1) else 0
                        sock_ref = self.sock
                        if sock_ref:
                            try:
                                sock_ref.send(make_ack(ack_seq))
                            except Exception:
                                pass
                        self._handle_payload(pld, dtype)
            except socket.timeout:
                continue
            except Exception:
                unexpected_drop = not self._manual_disconnect and not self._system_suspended
                break

        self.connected = False
        self.state["connected"] = False
        self.state["bat_l"] = 0
        self.state["bat_r"] = 0
        self.state["bat_case"] = 0
        self.notify_state()

        if unexpected_drop and not self._shutdown_flag:
            self._schedule_auto_reconnect()

    def _handle_payload(self, pld: bytes, dtype: int = 12) -> None:
        if not pld:
            return
        cmd = pld[0]

        if cmd == 0x05 and len(pld) >= 3:
            info_type = pld[1]
            str_len = pld[2]
            val = pld[3 : 3 + str_len].decode("utf-8", errors="ignore")
            if info_type == 0x01 and val:
                self.state["model"] = val
            elif info_type == 0x02 and val:
                self.state["fw_version"] = val

        elif cmd in (0x11, 0x13) and len(pld) >= 4:
            bat_type = pld[1]
            if bat_type == 0x01 and len(pld) >= 6:
                self.state["bat_l"] = min(100, max(0, pld[2]))
                self.state["bat_l_charging"] = pld[3] == 1
                self.state["bat_r"] = min(100, max(0, pld[4]))
                self.state["bat_r_charging"] = pld[5] == 1
            elif bat_type == 0x02 and len(pld) >= 4:
                self.state["bat_case"] = min(100, max(0, pld[2]))
                self.state["bat_case_charging"] = pld[3] == 1

        elif cmd in (0x15, 0x17) and len(pld) >= 3:
            is_in_ear = pld[2] == 0x01
            self.state["in_ear_detected"] = is_in_ear
            if self.state.get("wearing_pause") and self.on_wearing_event:
                self.on_wearing_event(is_in_ear)

        elif cmd in (0x19, 0x1B) and len(pld) >= 3:
            codec_id = pld[2]
            codecs = {0x00: "SBC", 0x01: "SBC", 0x02: "AAC", 0x03: "LDAC", 0x04: "aptX", 0x05: "aptX HD"}
            self.state["codec"] = codecs.get(codec_id, f"Codec {codec_id}")

        elif cmd in (0x57, 0x59) and len(pld) >= 4:
            if pld[1] == 0x01:
                preset_id = pld[2]
                self.state["eq_preset"] = EQ_ID_TO_NAME.get(preset_id, "Manual (Custom)")
                count = pld[3]
                if count >= 6 and len(pld) >= 4 + count:
                    cb = int(pld[4]) - 10
                    bds = [int(pld[5 + i]) - 10 for i in range(5)]
                    self.state["clear_bass"] = cb
                    self.state["eq_bands"] = bds
                    self._sync_apo_eq(str(self.state["eq_preset"]), cb, bds)

        elif cmd in (0x67, 0x69) and len(pld) >= 8:
            if pld[1] == 0x02:
                effect = pld[2]
                nc_val = pld[4]
                asm_id = pld[6]
                asm_val = pld[7]
                self.state["focus_on_voice"] = asm_id == 0x01
                if effect == 0x00:
                    self.state["nc_mode"] = "Desligado"
                elif effect == 0x01:
                    self.state["nc_mode"] = "ANC" if nc_val == 0x00 else "Vento"
                elif effect == 0x02:
                    self.state["nc_mode"] = "Ambiente"
                    self.state["asm_level"] = asm_val + 1

        elif cmd in (0xF7, 0xF9) and len(pld) >= 3:
            feat = pld[1]
            if feat == 0x01:
                self.state["conn_mode"] = (
                    "Prioridade na Conexão Estável" if pld[2] == 0x01 else "Prioridade na Qualidade do Som"
                )
            elif feat == 0x02:
                self.state["dsee_hx"] = pld[2] == 0x01
            elif feat == 0x03:
                self.state["wearing_pause"] = pld[2] == 0x01
            elif feat == 0x04:
                self.state["auto_off"] = AUTO_OFF_ID_TO_NAME.get(pld[2], "Não desligar")
            elif feat == 0x06 and len(pld) >= 4:
                self.state["touch_l"] = TOUCH_ID_TO_NAME.get(pld[2], "Controle de Som Ambiente")
                self.state["touch_r"] = TOUCH_ID_TO_NAME.get(pld[3], "Controle de Reprodução")

        self.notify_state()

    def query_all_states(self) -> None:
        queries: List[bytes] = [
            bytes([0x04, 0x01]),
            bytes([0x04, 0x02]),
            bytes([0x10, 0x01]),
            bytes([0x10, 0x02]),
            bytes([0x18]),
            bytes([0x56, 0x01]),
            bytes([0x66, 0x02]),
            bytes([0xF6, 0x01]),
            bytes([0xF6, 0x02]),
            bytes([0xF6, 0x03]),
            bytes([0xF6, 0x04]),
            bytes([0xF6, 0x06]),
        ]
        pause_sec = 0.005 if self.mock_mode else 0.035
        for q in queries:
            if not self.connected:
                break
            self.send_command(q)
            time.sleep(pause_sec)

    def set_nc_asm(self, mode: str, asm_level: int = 10, focus_voice: bool = False) -> None:
        self.state["nc_mode"] = mode
        self.state["asm_level"] = asm_level
        self.state["focus_on_voice"] = focus_voice

        effect = 0x01
        nc_val = 0x00
        asm_id = 0x01 if focus_voice else 0x00
        asm_val = max(0, min(19, int(asm_level) - 1))

        if mode == "ANC":
            effect, nc_val = 0x01, 0x00
        elif mode == "Vento":
            effect, nc_val = 0x01, 0x01
        elif mode == "Ambiente":
            effect = 0x02
        elif mode == "Desligado":
            effect = 0x00

        pld = bytes([0x68, 0x02, effect, 0x00, nc_val, 0x01, asm_id, asm_val])
        self.send_command(pld)
        self.send_command(bytes([0x66, 0x02]))

    def set_eq_custom(self, preset_name: str, clear_bass: int, bands: List[int]) -> None:
        clean_bands = [int(b) for b in list(bands)[:5]]
        while len(clean_bands) < 5:
            clean_bands.append(0)
        self.state["eq_preset"] = preset_name
        self.state["clear_bass"] = int(clear_bass)
        self.state["eq_bands"] = clean_bands
        self._sync_apo_eq(preset_name, int(clear_bass), clean_bands)

        preset_id = EQ_PRESETS.get(preset_name, 0xA0)
        cb_byte = max(0, min(20, int(clear_bass) + 10))
        band_bytes = [max(0, min(20, int(b) + 10)) for b in clean_bands]
        pld = bytes([0x58, 0x01, preset_id, 0x06, cb_byte] + band_bytes)
        self.send_command(pld)
        self.send_command(bytes([0x56, 0x01]))

    def set_eq_preset_only(self, preset_name: str) -> None:
        self.state["eq_preset"] = preset_name
        preset_id = EQ_PRESETS.get(preset_name, 0x00)
        if preset_id in MOCK_PRESET_CURVES:
            cb, bds = MOCK_PRESET_CURVES[preset_id]
            self._sync_apo_eq(preset_name, cb, list(bds))
        pld = bytes([0x58, 0x01, preset_id, 0x00])
        self.send_command(pld)
        self.send_command(bytes([0x56, 0x01]))

    def set_connection_mode(self, stable_priority: bool) -> None:
        val = 0x01 if stable_priority else 0x00
        self.send_command(bytes([0xF8, 0x01, 0x00, val]))
        self.send_command(bytes([0xF6, 0x01]))

    def set_dsee_hx(self, enabled: bool) -> None:
        val = 0x01 if enabled else 0x00
        self.send_command(bytes([0xF8, 0x02, 0x00, val]))
        self.send_command(bytes([0xF6, 0x02]))

    def set_wearing_pause(self, enabled: bool) -> None:
        val = 0x01 if enabled else 0x00
        self.send_command(bytes([0xF8, 0x03, 0x00, val]))
        self.send_command(bytes([0xF6, 0x03]))

    def set_auto_power_off(self, option_name: str) -> None:
        elem = AUTO_OFF_OPTIONS.get(option_name, 0x11)
        self.send_command(bytes([0xF8, 0x04, 0x01, elem, 0x00]))
        self.send_command(bytes([0xF6, 0x04]))

    def set_touch_sensors(self, left_name: str, right_name: str) -> None:
        l_id = TOUCH_OPTIONS.get(left_name, 0x10)
        r_id = TOUCH_OPTIONS.get(right_name, 0x00)
        self.send_command(bytes([0xF8, 0x06, 0x02, l_id, r_id]))
        self.send_command(bytes([0xF6, 0x06]))

    def power_off_headphones(self) -> None:
        self._manual_disconnect = True
        self._backoff_cancel_event.set()
        self.send_command(bytes([0x22, 0x00, 0x01]))


SonyMdrClient = SonyMdrV1Driver
