"""
Overlay Flutuante Nativo Windows 11 Estilo Apple iOS (Per-Pixel Alpha) — Sony Sound Connect PC
Autor: Matheus Veras
Licença: Source-Available Proprietary (Ver LICENSE.md)

Renderiza um card translúcido de alta definição (2x Supersampled LANCZOS) diretamente sobre a
área de trabalho ou jogos em tela cheia/borderless via Win32 `UpdateLayeredWindow`:
- Zero roubo de foco (`WS_EX_NOACTIVATE` + `SW_SHOWNOACTIVATE` + `MA_NOACTIVATEANDEAT`)
- Composição DWM por hardware com alfa pré-multiplicado (60+ FPS durante 220ms, 0.0% CPU em standby)
- Clique opcional sobre o card dispensa a animação instantaneamente sem minimizar o jogo ativo
"""

import ctypes
import ctypes.wintypes
import math
import os
import queue
import threading
import time
from typing import Any, Dict, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

LRESULT = ctypes.c_ssize_t
WPARAM = ctypes.c_size_t
LPARAM = ctypes.c_ssize_t
HWND = ctypes.wintypes.HWND
HDC = ctypes.wintypes.HDC
HBITMAP = ctypes.wintypes.HBITMAP
HGDIOBJ = ctypes.wintypes.HANDLE
HINSTANCE = ctypes.wintypes.HINSTANCE

WNDPROC = ctypes.WINFUNCTYPE(LRESULT, HWND, ctypes.wintypes.UINT, WPARAM, LPARAM)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", ctypes.wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", HINSTANCE),
        ("hIcon", ctypes.wintypes.HICON),
        ("hCursor", ctypes.wintypes.HANDLE),
        ("hbrBackground", ctypes.wintypes.HBRUSH),
        ("lpszMenuName", ctypes.wintypes.LPCWSTR),
        ("lpszClassName", ctypes.wintypes.LPCWSTR),
    ]


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class SIZE(ctypes.Structure):
    _fields_ = [("cx", ctypes.c_long), ("cy", ctypes.c_long)]


class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [
        ("BlendOp", ctypes.c_ubyte),
        ("BlendFlags", ctypes.c_ubyte),
        ("SourceConstantAlpha", ctypes.c_ubyte),
        ("AlphaFormat", ctypes.c_ubyte),
    ]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", ctypes.wintypes.DWORD),
        ("biWidth", ctypes.c_long),
        ("biHeight", ctypes.c_long),
        ("biPlanes", ctypes.wintypes.WORD),
        ("biBitCount", ctypes.wintypes.WORD),
        ("biCompression", ctypes.wintypes.DWORD),
        ("biSizeImage", ctypes.wintypes.DWORD),
        ("biXPelsPerMeter", ctypes.c_long),
        ("biYPelsPerMeter", ctypes.c_long),
        ("biClrUsed", ctypes.wintypes.DWORD),
        ("biClrImportant", ctypes.wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", ctypes.wintypes.DWORD * 3)]


# Assinaturas Win32 64-bit explícitas
user32.DefWindowProcW.argtypes = [HWND, ctypes.wintypes.UINT, WPARAM, LPARAM]
user32.DefWindowProcW.restype = LRESULT
user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
user32.RegisterClassW.restype = ctypes.wintypes.ATOM
user32.CreateWindowExW.argtypes = [
    ctypes.wintypes.DWORD,
    ctypes.wintypes.LPCWSTR,
    ctypes.wintypes.LPCWSTR,
    ctypes.wintypes.DWORD,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    HWND,
    ctypes.wintypes.HMENU,
    HINSTANCE,
    ctypes.wintypes.LPVOID,
]
user32.CreateWindowExW.restype = HWND
user32.ShowWindow.argtypes = [HWND, ctypes.c_int]
user32.ShowWindow.restype = ctypes.wintypes.BOOL
user32.DestroyWindow.argtypes = [HWND]
user32.DestroyWindow.restype = ctypes.wintypes.BOOL
user32.GetDC.argtypes = [HWND]
user32.GetDC.restype = HDC
user32.ReleaseDC.argtypes = [HWND, HDC]
user32.ReleaseDC.restype = ctypes.c_int
user32.UpdateLayeredWindow.argtypes = [
    HWND,
    HDC,
    ctypes.POINTER(POINT),
    ctypes.POINTER(SIZE),
    HDC,
    ctypes.POINTER(POINT),
    ctypes.wintypes.COLORREF,
    ctypes.POINTER(BLENDFUNCTION),
    ctypes.wintypes.DWORD,
]
user32.UpdateLayeredWindow.restype = ctypes.wintypes.BOOL
user32.SystemParametersInfoW.argtypes = [
    ctypes.wintypes.UINT,
    ctypes.wintypes.UINT,
    ctypes.c_void_p,
    ctypes.wintypes.UINT,
]
user32.SystemParametersInfoW.restype = ctypes.wintypes.BOOL
user32.PeekMessageW.argtypes = [
    ctypes.POINTER(ctypes.wintypes.MSG),
    HWND,
    ctypes.wintypes.UINT,
    ctypes.wintypes.UINT,
    ctypes.wintypes.UINT,
]
user32.PeekMessageW.restype = ctypes.wintypes.BOOL

gdi32.CreateCompatibleDC.argtypes = [HDC]
gdi32.CreateCompatibleDC.restype = HDC
gdi32.DeleteDC.argtypes = [HDC]
gdi32.DeleteDC.restype = ctypes.wintypes.BOOL
gdi32.CreateDIBSection.argtypes = [
    HDC,
    ctypes.POINTER(BITMAPINFO),
    ctypes.wintypes.UINT,
    ctypes.POINTER(ctypes.c_void_p),
    ctypes.wintypes.HANDLE,
    ctypes.wintypes.DWORD,
]
gdi32.CreateDIBSection.restype = HBITMAP
gdi32.SelectObject.argtypes = [HDC, HGDIOBJ]
gdi32.SelectObject.restype = HGDIOBJ
gdi32.DeleteObject.argtypes = [HGDIOBJ]
gdi32.DeleteObject.restype = ctypes.wintypes.BOOL
kernel32.GetModuleHandleW.argtypes = [ctypes.wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = HINSTANCE

WS_POPUP = 0x80000000
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_LAYERED = 0x00080000
WS_EX_NOACTIVATE = 0x08000000

SW_HIDE = 0
SW_SHOWNOACTIVATE = 4

WM_MOUSEACTIVATE = 0x0021
WM_LBUTTONDOWN = 0x0201
WM_RBUTTONDOWN = 0x0204
MA_NOACTIVATEANDEAT = 4

PM_REMOVE = 0x0001
SPI_GETWORKAREA = 0x0030
ULW_ALPHA = 0x00000002
AC_SRC_OVER = 0x00
AC_SRC_ALPHA = 0x01
BI_RGB = 0
DIB_RGB_COLORS = 0


def _load_win_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Carrega fonte nativa Segoe UI Variable / Segoe UI do Windows 11 com fallback seguro."""
    win_fonts = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    candidates = (
        ["SegoeUIVF.ttf", "segoeuib.ttf", "arialbd.ttf"]
        if bold
        else ["SegoeUIVF.ttf", "segoeui.ttf", "arial.ttf"]
    )
    for fname in candidates:
        fpath = os.path.join(win_fonts, fname)
        if os.path.exists(fpath):
            try:
                font = ImageFont.truetype(fpath, size)
                if fname == "SegoeUIVF.ttf":
                    try:
                        font.set_variation_by_name("Semibold" if bold else "Regular")
                    except Exception:
                        pass
                return font
            except Exception:
                continue
    return ImageFont.load_default()


def rgba_to_premultiplied_bgra(img: Image.Image) -> bytes:
    """
    Converte uma imagem RGBA Pillow em buffer BGRA de 32 bits com alfa pré-multiplicado
    usando composição SIMD nativa em C (< 0.5 ms para 376x206).
    """
    rgba = img.convert("RGBA")
    alpha = rgba.getchannel("A")
    black_bg = Image.new("RGB", rgba.size, (0, 0, 0))
    premul_rgb = Image.composite(rgba.convert("RGB"), black_bg, alpha)
    r, g, b = premul_rgb.split()
    return Image.merge("RGBA", (b, g, r, alpha)).tobytes()


class IosDesktopOverlay:
    """
    Pop-up nativo estilo Apple iOS / AirPods para Windows 11.
    Opera fora da janela principal (funciona mesmo quando minimizado na bandeja do sistema).
    """

    CARD_W: int = 416
    CARD_H: int = 260

    def __init__(self, assets_dir: str) -> None:
        self._assets_dir = assets_dir
        self._cmd_queue: "queue.Queue[Optional[Dict[str, Any]]]" = queue.Queue()
        self._dismiss_requested = threading.Event()
        self._shutdown_flag = False
        self._thumb_cache: Dict[str, Image.Image] = {}
        self._wndproc_ref: Optional[WNDPROC] = None
        self._worker_thread: Optional[threading.Thread] = None
        self._thread_lock = threading.Lock()

    def _ensure_worker(self) -> None:
        with self._thread_lock:
            if self._worker_thread is None or not self._worker_thread.is_alive():
                self._worker_thread = threading.Thread(
                    target=self._overlay_gui_loop,
                    name="SonyIosDesktopOverlay",
                    daemon=True,
                )
                self._worker_thread.start()

    def _get_cached_thumb(self, key: str, target_px: int = 92) -> Optional[Image.Image]:
        if key in self._thumb_cache:
            return self._thumb_cache[key]
        candidates_map = {
            "l": ["earbud_l_clean.png", "earbud_l_nano.png", "earbud_l.png", "app_icon_web.png"],
            "r": ["earbud_r_clean.png", "earbud_r_nano.png", "earbud_r.png", "app_icon_web.png"],
            "c": ["case_clean.png", "case_nano.png", "earbud_case.png", "app_icon_web.png"],
            "icon": ["app_icon_web.png", "app_icon.png"],
        }
        for fname in candidates_map.get(key, []):
            fpath = os.path.join(self._assets_dir, fname)
            if os.path.exists(fpath):
                try:
                    with Image.open(fpath) as raw:
                        rgba = raw.convert("RGBA")
                        rgba.thumbnail((target_px, target_px), Image.Resampling.LANCZOS)
                        self._thumb_cache[key] = rgba
                        return rgba
                except Exception:
                    continue
        return None

    def render_card_image(self, state: Dict[str, Any]) -> Image.Image:
        """
        Desenha o card translúcido com supersampling 2x para acabamento Retina ultra-nítido,
        com 3 caixas verticais idênticas ao design consolidado: ESQUERDO, ESTOJO (CENTRAL) e DIREITO.
        """
        scale = 2
        W = self.CARD_W * scale
        H = self.CARD_H * scale
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        pad = 12 * scale
        radius = 24 * scale

        # Sombra externa suave em camadas concêntricas
        for s_idx, alpha_val in enumerate((14, 26, 42)):
            grow = (3 - s_idx) * 3 * scale
            draw.rounded_rectangle(
                [pad - grow // 2, pad - grow // 2 + 4 * scale, W - pad + grow // 2, H - pad + grow // 2 + 6 * scale],
                radius=radius + grow // 2,
                fill=(3, 5, 10, alpha_val),
            )

        # Corpo principal Obsidian Glassmorphism (opacidade 99% para zero artefatos com o papel de parede)
        draw.rounded_rectangle(
            [pad, pad, W - pad, H - pad],
            radius=radius,
            fill=(14, 18, 27, 252),
            outline=(255, 255, 255, 34),
            width=2 * scale,
        )

        # Linha especular dourada no topo (acabamento Sony Premium / Apple HIG)
        gold_line_w = int(W * 0.55)
        gx1 = (W - gold_line_w) // 2
        gx2 = gx1 + gold_line_w
        draw.line([(gx1, pad + 1), (gx2, pad + 1)], fill=(229, 193, 120, 160), width=1 * scale)

        font_title = _load_win_font(15 * scale, bold=True)
        font_sub = _load_win_font(9 * scale, bold=True)
        font_badge = _load_win_font(8 * scale, bold=True)
        font_pct = _load_win_font(12 * scale, bold=True)
        font_slot_lbl = _load_win_font(9 * scale, bold=True)
        font_chg = _load_win_font(8 * scale, bold=True)

        model = str(state.get("model") or "WF-1000XM3").replace("(Mock)", "").strip()
        if len(model) > 24:
            model = model[:23] + "…"
        nc_mode = str(state.get("nc_mode") or "ANC")
        codec = str(state.get("codec") or "AAC")
        is_conn = bool(state.get("connected", True))

        # Cabeçalho: Ponto LED de status com halo difuso
        led_color = (16, 185, 129, 255) if is_conn else (245, 158, 11, 255)
        cx_led = pad + 18 * scale
        cy_led = pad + 20 * scale
        draw.ellipse([cx_led - 7 * scale, cy_led - 7 * scale, cx_led + 7 * scale, cy_led + 7 * scale], fill=(led_color[0], led_color[1], led_color[2], 65))
        draw.ellipse([cx_led - 4 * scale, cy_led - 4 * scale, cx_led + 4 * scale, cy_led + 4 * scale], fill=led_color)

        draw.text((pad + 30 * scale, pad + 11 * scale), model, font=font_title, fill=(248, 250, 252, 255))

        # Subtítulo Push em Ciano Elétrico (Codec + Cancelamento de Ruído / Vento / Ambiente)
        nc_lower = nc_mode.strip().lower()
        if "vento" in nc_lower or "wind" in nc_lower:
            mode_desc = "VENTO ATIVO"
        elif "anc" in nc_lower or "cancelamento" in nc_lower or "noise" in nc_lower:
            mode_desc = "CANCELAMENTO DE RUÍDO (ANC)"
        elif "ambiente" in nc_lower or "ambient" in nc_lower:
            asm_lvl = state.get("asm_level", 10)
            mode_desc = f"SOM AMBIENTE (NÍVEL {asm_lvl})"
        elif "desligado" in nc_lower or "off" in nc_lower:
            mode_desc = "SOM DESLIGADO"
        else:
            mode_desc = f"{nc_mode.upper()} ATIVO"

        subtitle = f"{codec.upper()} • {mode_desc}"
        draw.text((pad + 30 * scale, pad + 32 * scale), subtitle, font=font_sub, fill=(0, 229, 255, 240))

        # Pílula superior direita (CONECTADO em dourado / DESCONECTADO em vermelho)
        pill_w = 96 * scale
        pill_h = 24 * scale
        pill_x1 = W - pad - pill_w - 14 * scale
        pill_y1 = pad + 14 * scale
        pill_x2 = pill_x1 + pill_w
        pill_y2 = pill_y1 + pill_h

        pill_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        pdraw = ImageDraw.Draw(pill_layer)
        badge_bg = (197, 160, 89, 36) if is_conn else (239, 68, 68, 30)
        badge_border = (197, 160, 89, 140) if is_conn else (239, 68, 68, 140)
        badge_col = (229, 193, 120, 255) if is_conn else (248, 113, 113, 255)
        badge_txt = "CONECTADO" if is_conn else "DESCONECTADO"

        pdraw.rounded_rectangle(
            [pill_x1, pill_y1, pill_x2, pill_y2],
            radius=12 * scale,
            fill=badge_bg,
            outline=badge_border,
            width=1 * scale,
        )
        try:
            bb = pdraw.textbbox((0, 0), badge_txt, font=font_badge)
            bw = bb[2] - bb[0]
            bh = bb[3] - bb[1]
        except Exception:
            bw, bh = 50 * scale, 10 * scale
        pdraw.text((pill_x1 + (pill_w - bw) // 2, pill_y1 + (pill_h - bh) // 2 - 1 * scale), badge_txt, font=font_badge, fill=badge_col)
        canvas.alpha_composite(pill_layer)

        # 3 Slots Verticais no Layout Correto: ESQUERDO, ESTOJO (NO CENTRO), DIREITO
        bat_l = max(0, min(100, int(state.get("bat_l") or 0))) if is_conn else 0
        bat_r = max(0, min(100, int(state.get("bat_r") or 0))) if is_conn else 0
        bat_c = max(0, min(100, int(state.get("bat_case") or 0))) if is_conn else 0

        slots = [
            ("ESQUERDO", bat_l, bool(state.get("bat_l_charging")), "l", False),
            ("ESTOJO", bat_c, bool(state.get("bat_case_charging")), "c", True),
            ("DIREITO", bat_r, bool(state.get("bat_r_charging")), "r", False),
        ]

        inner_w = W - 2 * pad - 24 * scale
        gap = 10 * scale
        slot_w = (inner_w - 2 * gap) // 3
        slot_h = 176 * scale
        slot_y1 = pad + 54 * scale
        slot_y2 = slot_y1 + slot_h

        # Camada translúcida das caixas dos 3 slots com alfa pré-calculado
        boxes_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        bdraw = ImageDraw.Draw(boxes_layer)
        for idx in range(3):
            sx1 = pad + 12 * scale + idx * (slot_w + gap)
            sx2 = sx1 + slot_w
            bdraw.rounded_rectangle(
                [sx1, slot_y1, sx2, slot_y2],
                radius=16 * scale,
                fill=(255, 255, 255, 9),
                outline=(255, 255, 255, 20),
                width=1 * scale,
            )
        canvas.alpha_composite(boxes_layer)

        # Camada de anéis e textos para perfeita nitidez
        gauges_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(gauges_layer)

        for idx, (label, pct, charging, asset_key, is_case) in enumerate(slots):
            sx1 = pad + 12 * scale + idx * (slot_w + gap)
            sx2 = sx1 + slot_w
            scx = (sx1 + sx2) // 2

            # 1. Render 3D do Fone / Estojo
            thumb = self._get_cached_thumb(asset_key, target_px=54 * scale)
            if thumb is not None:
                tx = scx - thumb.width // 2
                ty = slot_y1 + 10 * scale + (48 * scale - thumb.height) // 2
                canvas.alpha_composite(thumb, (tx, ty))

            # 2. Anel de Bateria Apple iOS Circular
            ring_cy = slot_y1 + 95 * scale
            ring_r = 23 * scale
            ring_thick = 3.5 * scale
            bbox = [scx - ring_r, ring_cy - ring_r, scx + ring_r, ring_cy + ring_r]

            # Trilho de fundo
            gdraw.arc(bbox, start=0, end=360, fill=(255, 255, 255, 26), width=int(ring_thick))

            # Arco ativo proporcional
            if pct > 0:
                if is_case:
                    arc_col = (229, 193, 120, 255)  # Cobre/Dourado exclusivo do Estojo
                elif pct <= 20:
                    arc_col = (239, 68, 68, 255)
                elif pct < 35:
                    arc_col = (245, 158, 11, 255)
                else:
                    arc_col = (16, 185, 129, 255)
                sweep = max(8.0, (pct / 100.0) * 360.0)
                gdraw.arc(bbox, start=-90, end=-90 + sweep, fill=arc_col, width=int(ring_thick))

            # Porcentagem dentro do anel (ex: 100%, 70%, --%)
            pct_text = f"{pct}%" if pct > 0 else "--%"
            col_pct = (241, 245, 249, 255) if pct > 20 else ((252, 165, 165, 255) if pct > 0 else (148, 163, 184, 180))
            try:
                pb = gdraw.textbbox((0, 0), pct_text, font=font_pct)
                pw = pb[2] - pb[0]
                ph = pb[3] - pb[1]
            except Exception:
                pw, ph = 30 * scale, 12 * scale
            gdraw.text((scx - pw // 2, ring_cy - ph // 2 - 1 * scale), pct_text, font=font_pct, fill=col_pct)

            # 3. Rótulo inferior (ESQUERDO, ESTOJO, DIREITO)
            try:
                lb = gdraw.textbbox((0, 0), label, font=font_slot_lbl)
                lw = lb[2] - lb[0]
            except Exception:
                lw = 40 * scale
            gdraw.text((scx - lw // 2, slot_y1 + 134 * scale), label, font=font_slot_lbl, fill=(148, 163, 184, 230))

            # 4. Tag de Carregamento ⚡
            if charging:
                chg_txt = "⚡ CARREGANDO"
                try:
                    cb = gdraw.textbbox((0, 0), chg_txt, font=font_chg)
                    cw = cb[2] - cb[0]
                except Exception:
                    cw = 30 * scale
                chg_col = (229, 193, 120, 255) if is_case else (16, 185, 129, 255)
                gdraw.text((scx - cw // 2, slot_y1 + 152 * scale), chg_txt, font=font_chg, fill=chg_col)

        canvas.alpha_composite(gauges_layer)
        return canvas.resize((self.CARD_W, self.CARD_H), Image.Resampling.LANCZOS)

    def show(self, state: Dict[str, Any], hold_seconds: float = 4.4) -> None:
        """Dispara ou atualiza suavemente o pop-up flutuante sobre o Windows 11 sem roubar foco."""
        self._ensure_worker()
        snapshot = dict(state)
        snapshot["_hold_seconds"] = max(1.0, float(hold_seconds))
        self._dismiss_requested.clear()
        self._cmd_queue.put(snapshot)

    def dismiss(self) -> None:
        """Dispensa imediatamente o overlay atual."""
        self._dismiss_requested.set()

    def shutdown(self) -> None:
        """Encerra de forma limpa a janela layered e a thread dedicada."""
        self._shutdown_flag = True
        self._dismiss_requested.set()
        self._cmd_queue.put(None)

    def _get_target_bottom_right(self) -> Tuple[int, int]:
        rect = ctypes.wintypes.RECT()
        if user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0):
            x = rect.right - self.CARD_W - 18
            y = rect.bottom - self.CARD_H - 18
            return (x, y)
        screen_w = user32.GetSystemMetrics(0)
        screen_h = user32.GetSystemMetrics(1)
        return (screen_w - self.CARD_W - 20, screen_h - self.CARD_H - 64)

    def _overlay_gui_loop(self) -> None:
        hinst = kernel32.GetModuleHandleW(None)
        cls_name = f"SonyIosOverlayLayered_{os.getpid()}_{kernel32.GetCurrentThreadId()}"

        def _wnd_proc(hwnd: int, msg: int, wparam: int, lparam: int) -> int:
            if msg == WM_MOUSEACTIVATE:
                self._dismiss_requested.set()
                return MA_NOACTIVATEANDEAT
            if msg in (WM_LBUTTONDOWN, WM_RBUTTONDOWN):
                self._dismiss_requested.set()
                return 0
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        self._wndproc_ref = WNDPROC(_wnd_proc)
        wc = WNDCLASSW()
        wc.lpfnWndProc = self._wndproc_ref
        wc.hInstance = hinst
        wc.lpszClassName = cls_name
        user32.RegisterClassW(ctypes.byref(wc))

        ex_style = WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
        hwnd = user32.CreateWindowExW(
            ex_style,
            cls_name,
            "SonySoundConnectIosOverlay",
            WS_POPUP,
            0,
            0,
            self.CARD_W,
            self.CARD_H,
            None,
            None,
            hinst,
            None,
        )
        if not hwnd:
            return

        screen_dc = user32.GetDC(None)
        mem_dc = gdi32.CreateCompatibleDC(screen_dc)

        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = self.CARD_W
        bmi.bmiHeader.biHeight = -self.CARD_H  # Top-down DIB
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = BI_RGB

        bits_ptr = ctypes.c_void_p()
        dib_bmp = gdi32.CreateDIBSection(
            screen_dc,
            ctypes.byref(bmi),
            DIB_RGB_COLORS,
            ctypes.byref(bits_ptr),
            None,
            0,
        )
        old_bmp = gdi32.SelectObject(mem_dc, dib_bmp)
        user32.ReleaseDC(None, screen_dc)

        win_size = SIZE(self.CARD_W, self.CARD_H)
        pt_src = POINT(0, 0)
        msg = ctypes.wintypes.MSG()

        def _pump_pending_messages() -> None:
            while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_REMOVE):
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))

        def _push_layered_frame(x: int, y: int, alpha_byte: int) -> None:
            s_dc = user32.GetDC(None)
            try:
                pt_dst = POINT(x, y)
                blend = BLENDFUNCTION(AC_SRC_OVER, 0, max(0, min(255, alpha_byte)), AC_SRC_ALPHA)
                user32.UpdateLayeredWindow(
                    hwnd,
                    s_dc,
                    ctypes.byref(pt_dst),
                    ctypes.byref(win_size),
                    mem_dc,
                    ctypes.byref(pt_src),
                    0,
                    ctypes.byref(blend),
                    ULW_ALPHA,
                )
            finally:
                user32.ReleaseDC(None, s_dc)

        try:
            while not self._shutdown_flag:
                # 0.00% CPU em repouso absoluto até chegar um comando show()
                payload = self._cmd_queue.get()
                if payload is None or self._shutdown_flag:
                    break

                # Coalesce múltiplos pedidos enfileirados em sequência
                while not self._cmd_queue.empty():
                    try:
                        nxt = self._cmd_queue.get_nowait()
                        if nxt is None:
                            self._shutdown_flag = True
                            break
                        payload = nxt
                    except queue.Empty:
                        break
                if self._shutdown_flag:
                    break

                card_img = self.render_card_image(payload)
                bgra_bytes = rgba_to_premultiplied_bgra(card_img)
                if bits_ptr.value:
                    ctypes.memmove(bits_ptr.value, bgra_bytes, len(bgra_bytes))

                base_x, base_y = self._get_target_bottom_right()
                slide_px = 20

                # Frame inicial invisível antes de exibir a janela
                _push_layered_frame(base_x, base_y + slide_px, 0)
                user32.ShowWindow(hwnd, SW_SHOWNOACTIVATE)

                # Animação de Entrada (220ms cubic-out — Apple Fluid Design)
                enter_dur = 0.22
                t0 = time.perf_counter()
                while not self._dismiss_requested.is_set() and not self._shutdown_flag:
                    elapsed = time.perf_counter() - t0
                    t = min(1.0, elapsed / enter_dur)
                    eased = 1.0 - math.pow(1.0 - t, 3.0)
                    cur_y = int(round(base_y + slide_px * (1.0 - eased)))
                    cur_a = int(round(255 * eased))
                    _push_layered_frame(base_x, cur_y, cur_a)
                    _pump_pending_messages()
                    if t >= 1.0:
                        break
                    time.sleep(0.014)

                # Permanência (interrompível instantaneamente por clique ou atualização de estado)
                hold_dur = float(payload.get("_hold_seconds", 4.4))
                hold_start = time.perf_counter()
                while (
                    not self._dismiss_requested.is_set()
                    and not self._shutdown_flag
                    and (time.perf_counter() - hold_start) < hold_dur
                ):
                    if not self._cmd_queue.empty():
                        break
                    _pump_pending_messages()
                    time.sleep(0.04)

                # Se já há novo estado na fila, atualiza in-place sem fechar!
                if not self._cmd_queue.empty() and not self._dismiss_requested.is_set():
                    continue

                # Animação de Saída (170ms ease-out simétrica na mesma trajetória)
                exit_dur = 0.17
                t1 = time.perf_counter()
                while not self._shutdown_flag:
                    elapsed = time.perf_counter() - t1
                    t = min(1.0, elapsed / exit_dur)
                    eased = 1.0 - math.pow(1.0 - t, 2.5)
                    cur_y = int(round(base_y + (slide_px * 0.65) * eased))
                    cur_a = int(round(255 * (1.0 - eased)))
                    _push_layered_frame(base_x, cur_y, cur_a)
                    _pump_pending_messages()
                    if t >= 1.0:
                        break
                    time.sleep(0.014)

                user32.ShowWindow(hwnd, SW_HIDE)
                self._dismiss_requested.clear()
        finally:
            try:
                user32.ShowWindow(hwnd, SW_HIDE)
                gdi32.SelectObject(mem_dc, old_bmp)
                if dib_bmp:
                    gdi32.DeleteObject(dib_bmp)
                if mem_dc:
                    gdi32.DeleteDC(mem_dc)
                user32.DestroyWindow(hwnd)
            except Exception:
                pass
