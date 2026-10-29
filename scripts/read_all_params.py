import socket
import struct

mac = "14:3F:A6:5D:DF:D5"

def escape_specials(data: bytes) -> bytes:
    res = bytearray()
    for b in data:
        if b == 60: res.extend([61, 44])
        elif b == 61: res.extend([61, 45])
        elif b == 62: res.extend([61, 46])
        else: res.append(b)
    return bytes(res)

def unescape_specials(data: bytes) -> bytes:
    res = bytearray()
    i = 0
    while i < len(data):
        b = data[i]
        if b == 61 and i + 1 < len(data):
            nxt = data[i+1]
            if nxt == 44: res.append(60)
            elif nxt == 45: res.append(61)
            elif nxt == 46: res.append(62)
            i += 2
        else:
            res.append(b)
            i += 1
    return bytes(res)

def make_packet(payload: bytes, data_type=12, seq=0):
    header_and_payload = struct.pack(">BBI", data_type, seq, len(payload)) + payload
    chk = sum(header_and_payload) & 0xFF
    body = header_and_payload + bytes([chk])
    return b"\x3E" + escape_specials(body) + b"\x3C"

def make_ack(seq: int):
    return make_packet(b"", data_type=1, seq=seq)

s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
s.settimeout(15.0)
s.connect((mac, 9))
s.settimeout(0.8)

def send_cmd(name: str, payload: bytes, seq: int):
    pkt = make_packet(payload, data_type=12, seq=seq)
    s.send(pkt)
    buf = b""
    for _ in range(6):
        try:
            chunk = s.recv(1024)
            if not chunk: break
            buf += chunk
            while b"\x3E" in buf and b"\x3C" in buf:
                start = buf.index(b"\x3E")
                end = buf.index(b"\x3C", start)
                frame = buf[start+1:end]
                buf = buf[end+1:]
                un = unescape_specials(frame)
                dtype = un[0]
                rseq = un[1]
                plen = struct.unpack(">I", un[2:6])[0]
                pld = un[6:6+plen]
                if dtype != 1:
                    ack_seq = 1 - rseq if rseq in (0, 1) else 0
                    s.send(make_ack(ack_seq))
                    print(f"[{name}] -> {pld.hex()}")
                    return pld
        except socket.timeout:
            break
    return None

seq = 0
send_cmd("Init Protocol", bytes([0x00, 0x00]), seq); seq = 1 - seq
send_cmd("Audio Codec (0x18)", bytes([0x18, 0x02]), seq); seq = 1 - seq
send_cmd("Upscaling Effect (0x14)", bytes([0x14, 0x00]), seq); seq = 1 - seq
send_cmd("EQ Param (0x56, 0x01)", bytes([0x56, 0x01]), seq); seq = 1 - seq
send_cmd("NC/ASM Param (0x66, 0x02)", bytes([0x66, 0x02]), seq); seq = 1 - seq
send_cmd("Audio Param ConnMode (0xE6, 0x01)", bytes([0xE6, 0x01]), seq); seq = 1 - seq
send_cmd("Audio Param DSEE (0xE6, 0x02)", bytes([0xE6, 0x02]), seq); seq = 1 - seq
send_cmd("System Wearing (0xF6, 0x03)", bytes([0xF6, 0x03]), seq); seq = 1 - seq
send_cmd("System AutoOff (0xF6, 0x04)", bytes([0xF6, 0x04]), seq); seq = 1 - seq
send_cmd("System Touch (0xF6, 0x06)", bytes([0xF6, 0x06]), seq); seq = 1 - seq
s.close()
