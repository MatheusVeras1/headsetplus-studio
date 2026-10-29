"""
Módulo de Integração Nativa com o Windows 11 — Sony Sound Connect PC / Universal Audio Hub
Autor: Matheus Veras
Licença: Source-Available Proprietary (Ver LICENSE.md)

Funcionalidades (Arquitetura Event-Driven — 0.0% de CPU em Standby):
1. Atalhos Globais de Teclado (Global Hotkeys) via Win32 RegisterHotKey (Ctrl+Shift+A para ANC, Ctrl+Shift+E para EQ)
2. Controle Inteligente de Mídia por Detecção de Uso (In-Ear Auto-Pause / Auto-Play via VK_MEDIA_PLAY_PAUSE)
3. Automação Editável de Combos Acústicos por Aplicativo (EQ + ANC/Ambiente + Crossfeed 3D) via SetWinEventHook
4. Interceptação de Suspensão/Hibernação do Windows 11 (WM_POWERBROADCAST: PBT_APMSUSPEND / PBT_APMRESUMEAUTOMATIC)
5. Auto-Conexão Zero-Click ao Abrir o Estojo Bluetooth via Kernel Event `WM_DEVICECHANGE` (`DBT_DEVNODES_CHANGED`)
"""

import ctypes
import ctypes.wintypes
import os
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

# Tipos Win32 seguros para arquiteturas 64-bit (Windows 11 x64 / ARM64)
LRESULT = ctypes.c_ssize_t
WPARAM = ctypes.c_size_t
LPARAM = ctypes.c_ssize_t
HWND = ctypes.wintypes.HWND
HINSTANCE = ctypes.wintypes.HINSTANCE
HWINEVENTHOOK = ctypes.wintypes.HANDLE

WNDPROC = ctypes.WINFUNCTYPE(LRESULT, HWND, ctypes.wintypes.UINT, WPARAM, LPARAM)
WINEVENTPROC = ctypes.WINFUNCTYPE(
    None,
    HWINEVENTHOOK,
    ctypes.wintypes.DWORD,
    HWND,
    ctypes.wintypes.LONG,
    ctypes.wintypes.LONG,
    ctypes.wintypes.DWORD,
    ctypes.wintypes.DWORD,
)


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


# Assinaturas explícitas Win32 para evitar truncamento de ponteiros 64-bit
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
user32.DestroyWindow.argtypes = [HWND]
user32.DestroyWindow.restype = ctypes.wintypes.BOOL
user32.PostMessageW.argtypes = [HWND, ctypes.wintypes.UINT, WPARAM, LPARAM]
user32.PostMessageW.restype = ctypes.wintypes.BOOL
user32.PostThreadMessageW.argtypes = [ctypes.wintypes.DWORD, ctypes.wintypes.UINT, WPARAM, LPARAM]
user32.PostThreadMessageW.restype = ctypes.wintypes.BOOL
user32.SetWinEventHook.argtypes = [
    ctypes.wintypes.DWORD,
    ctypes.wintypes.DWORD,
    ctypes.wintypes.HMODULE,
    WINEVENTPROC,
    ctypes.wintypes.DWORD,
    ctypes.wintypes.DWORD,
    ctypes.wintypes.DWORD,
]
user32.SetWinEventHook.restype = HWINEVENTHOOK
user32.UnhookWinEvent.argtypes = [HWINEVENTHOOK]
user32.UnhookWinEvent.restype = ctypes.wintypes.BOOL
kernel32.GetModuleHandleW.argtypes = [ctypes.wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = HINSTANCE

# Constantes Win32
VK_MEDIA_PLAY_PAUSE = 0xB3
KEYEVENTF_KEYUP = 0x0002
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_NOREPEAT = 0x4000

WM_CLOSE = 0x0010
WM_QUIT = 0x0012
WM_POWERBROADCAST = 0x0218
WM_DEVICECHANGE = 0x0219
WM_HOTKEY = 0x0312

PBT_APMSUSPEND = 0x0004
PBT_APMRESUMESUSPEND = 0x0007
PBT_APMRESUMEAUTOMATIC = 0x0012

DBT_DEVNODES_CHANGED = 0x0007
DBT_DEVICEARRIVAL = 0x8000

WS_POPUP = 0x80000000
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000

EVENT_SYSTEM_FOREGROUND = 0x0003
WINEVENT_OUTOFCONTEXT = 0x0000
WINEVENT_SKIPOWNPROCESS = 0x0002

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

HOTKEY_ID_NC = 101
HOTKEY_ID_EQ = 102

# Regras Padrão de Automação Completa (Combo EQ + ANC/Ambiente + Palco 3D)
DEFAULT_AUTOMATION_RULES: List[Dict[str, Any]] = [
    {
        "exe": "cs2.exe",
        "label": "Counter-Strike 2",
        "icon": "🎮",
        "eq_preset": "Gaming FPS (Passos)",
        "nc_mode": "ANC",
        "asm_level": 10,
        "focus_voice": False,
        "spatial_mode": "esports",
    },
    {
        "exe": "valorant.exe",
        "label": "Valorant",
        "icon": "🎮",
        "eq_preset": "Gaming FPS (Passos)",
        "nc_mode": "ANC",
        "asm_level": 10,
        "focus_voice": False,
        "spatial_mode": "esports",
    },
    {
        "exe": "r5apex.exe",
        "label": "Apex Legends",
        "icon": "🎮",
        "eq_preset": "Gaming FPS (Passos)",
        "nc_mode": "ANC",
        "asm_level": 10,
        "focus_voice": False,
        "spatial_mode": "esports",
    },
    {
        "exe": "cod.exe",
        "label": "Call of Duty",
        "icon": "🎮",
        "eq_preset": "Gaming FPS (Passos)",
        "nc_mode": "ANC",
        "asm_level": 10,
        "focus_voice": False,
        "spatial_mode": "esports",
    },
    {
        "exe": "spotify.exe",
        "label": "Spotify",
        "icon": "🎵",
        "eq_preset": "Audiófilo (Comunidade)",
        "nc_mode": "ANC",
        "asm_level": 10,
        "focus_voice": False,
        "spatial_mode": "hifi",
    },
    {
        "exe": "tidal.exe",
        "label": "TIDAL HiFi",
        "icon": "🎵",
        "eq_preset": "Audiófilo (Comunidade)",
        "nc_mode": "ANC",
        "asm_level": 10,
        "focus_voice": False,
        "spatial_mode": "hifi",
    },
    {
        "exe": "discord.exe",
        "label": "Discord (Voz + Transparência)",
        "icon": "🎙️",
        "eq_preset": "Voz & Podcast",
        "nc_mode": "Ambiente",
        "asm_level": 14,
        "focus_voice": True,
        "spatial_mode": "nearfield",
    },
    {
        "exe": "teams.exe",
        "label": "Microsoft Teams",
        "icon": "🎙️",
        "eq_preset": "Voz & Podcast",
        "nc_mode": "Ambiente",
        "asm_level": 13,
        "focus_voice": True,
        "spatial_mode": "nearfield",
    },
    {
        "exe": "zoom.exe",
        "label": "Zoom Meetings",
        "icon": "🎙️",
        "eq_preset": "Voz & Podcast",
        "nc_mode": "Ambiente",
        "asm_level": 13,
        "focus_voice": True,
        "spatial_mode": "nearfield",
    },
    {
        "exe": "vlc.exe",
        "label": "VLC Media Player",
        "icon": "🎬",
        "eq_preset": "Cinema Sub-Bass",
        "nc_mode": "ANC",
        "asm_level": 10,
        "focus_voice": False,
        "spatial_mode": "hifi",
    },
    {
        "exe": "netflix.exe",
        "label": "Netflix",
        "icon": "🎬",
        "eq_preset": "Cinema Sub-Bass",
        "nc_mode": "ANC",
        "asm_level": 10,
        "focus_voice": False,
        "spatial_mode": "hifi",
    },
    {
        "exe": "stremio.exe",
        "label": "Stremio",
        "icon": "🎬",
        "eq_preset": "Cinema Sub-Bass",
        "nc_mode": "ANC",
        "asm_level": 10,
        "focus_voice": False,
        "spatial_mode": "hifi",
    },
]

# Mapeamento legado preservado para compatibilidade retroativa
APP_PROFILE_MAPPING: Dict[str, Tuple[str, str]] = {
    r["exe"]: (r["eq_preset"], f"{r['icon']} {r['label']}: {r['eq_preset']} + {r['nc_mode']}")
    for r in DEFAULT_AUTOMATION_RULES
}


def normalize_automation_rule(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Valida e normaliza uma regra de automação por processo."""
    exe = str(raw.get("exe") or "").strip().lower()
    if not exe:
        return None
    if not exe.endswith(".exe"):
        exe += ".exe"
    label = str(raw.get("label") or exe.replace(".exe", "").capitalize()).strip()[:44]
    icon = str(raw.get("icon") or "⚡").strip()[:4] or "⚡"
    eq_preset = str(raw.get("eq_preset") or "Audiófilo (Comunidade)").strip()
    nc_mode = str(raw.get("nc_mode") or "Manter").strip()
    if nc_mode not in ("ANC", "Ambiente", "Vento", "Desligado", "Manter"):
        nc_mode = "ANC"
    asm_level = max(1, min(20, int(raw.get("asm_level") or 12)))
    focus_voice = bool(raw.get("focus_voice", False))
    spatial_mode = str(raw.get("spatial_mode") or "nearfield").strip().lower()
    if spatial_mode not in ("nearfield", "hifi", "esports", "off", "keep"):
        spatial_mode = "nearfield"

    return {
        "exe": exe,
        "label": label,
        "icon": icon,
        "eq_preset": eq_preset,
        "nc_mode": nc_mode,
        "asm_level": asm_level,
        "focus_voice": focus_voice,
        "spatial_mode": spatial_mode,
    }


def set_process_priority(high_priority: bool) -> None:
    """Ajusta a prioridade do processo (HIGH_PRIORITY_CLASS para jogos vs NORMAL_PRIORITY_CLASS)."""
    try:
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.GetCurrentProcess.restype = ctypes.c_void_p
        k32.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        p_class = 0x00000080 if high_priority else 0x00000020
        k32.SetPriorityClass(k32.GetCurrentProcess(), p_class)
    except Exception:
        pass


def trigger_windows_media_play_pause() -> None:
    """Simula pressionamento da tecla global de mídia Play/Pause do Windows."""
    try:
        user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
        user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, KEYEVENTF_KEYUP, 0)
    except Exception:
        pass


def get_process_name_from_hwnd(hwnd: Optional[int] = None) -> str:
    """Retorna o nome do executável de um HWND específico (ou da janela ativa em primeiro plano)."""
    try:
        target_hwnd = hwnd or user32.GetForegroundWindow()
        if not target_hwnd:
            return ""
        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(target_hwnd, ctypes.byref(pid))
        if not pid.value:
            return ""
        h_proc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if not h_proc:
            return ""
        try:
            buf = ctypes.create_unicode_buffer(512)
            size = ctypes.c_ulong(512)
            if kernel32.QueryFullProcessImageNameW(h_proc, 0, buf, ctypes.byref(size)):
                return os.path.basename(buf.value).lower()
            return ""
        finally:
            kernel32.CloseHandle(h_proc)
    except Exception:
        return ""


def get_foreground_process_name() -> str:
    """Compatibilidade direta: retorna o executável da janela atual em primeiro plano."""
    return get_process_name_from_hwnd(None)


class SystemIntegrationManager:
    """
    Gerencia atalhos globais, automação de combos por processo via hook de eventos Win32,
    auto-conexão Bluetooth Zero-Click (`WM_DEVICECHANGE`), energia (Sleep/Resume) e sensor auricular.
    """

    def __init__(
        self,
        on_toggle_nc: Optional[Callable[[], None]] = None,
        on_cycle_eq: Optional[Callable[[], None]] = None,
        on_apply_preset: Optional[Callable[[str, str], None]] = None,
        on_apply_automation_rule: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_toast: Optional[Callable[[str, str], None]] = None,
        on_system_suspend: Optional[Callable[[], None]] = None,
        on_system_resume: Optional[Callable[[], None]] = None,
        on_bluetooth_device_event: Optional[Callable[[], None]] = None,
        initial_rules: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.on_toggle_nc = on_toggle_nc
        self.on_cycle_eq = on_cycle_eq
        self.on_apply_preset = on_apply_preset
        self.on_apply_automation_rule = on_apply_automation_rule
        self.on_toast = on_toast
        self.on_system_suspend = on_system_suspend
        self.on_system_resume = on_system_resume
        self.on_bluetooth_device_event = on_bluetooth_device_event

        self.running: bool = False
        self.last_wearing_state: Optional[bool] = None
        self.current_fg_app: str = ""
        self.auto_profile_enabled: bool = True

        self._rules_lock = threading.Lock()
        self._rules_by_exe: Dict[str, Dict[str, Any]] = {}
        self.set_automation_rules(initial_rules or DEFAULT_AUTOMATION_RULES)

        self._event_thread: Optional[threading.Thread] = None
        self._pump_tid: int = 0
        self._sink_hwnd: Optional[int] = None
        self._last_resume_ts: float = 0.0

        # Debounce Timer para explosões de eventos PnP `WM_DEVICECHANGE` ao retirar fones do estojo
        self._devchange_lock = threading.Lock()
        self._devchange_timer: Optional[threading.Timer] = None

        # Referências fortes para impedir coleta de lixo (GC) dos ponteiros de callback C
        self._wndproc_ref: Optional[WNDPROC] = None
        self._winevent_proc_ref: Optional[WINEVENTPROC] = None

    def set_automation_rules(self, rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Substitui em memória a tabela de automação de combos por aplicativo."""
        cleaned: Dict[str, Dict[str, Any]] = {}
        for item in rules:
            norm = normalize_automation_rule(item)
            if norm:
                cleaned[norm["exe"]] = norm
        with self._rules_lock:
            self._rules_by_exe = cleaned
        return self.get_automation_rules()

    def get_automation_rules(self) -> List[Dict[str, Any]]:
        with self._rules_lock:
            return [dict(r) for r in self._rules_by_exe.values()]

    def upsert_automation_rule(self, rule: Dict[str, Any]) -> List[Dict[str, Any]]:
        norm = normalize_automation_rule(rule)
        if norm:
            with self._rules_lock:
                self._rules_by_exe[norm["exe"]] = norm
        return self.get_automation_rules()

    def remove_automation_rule(self, exe_name: str) -> List[Dict[str, Any]]:
        key = (exe_name or "").strip().lower()
        if key and not key.endswith(".exe"):
            key += ".exe"
        with self._rules_lock:
            self._rules_by_exe.pop(key, None)
        return self.get_automation_rules()

    def start(self) -> None:
        """Inicia o message pump unificado Win32 (0.0% de CPU em repouso)."""
        if self.running:
            return
        self.running = True
        self._event_thread = threading.Thread(
            target=self._win32_event_pump_worker,
            name="SonyWin32EventPump",
            daemon=True,
        )
        self._event_thread.start()

    def stop(self) -> None:
        """Solicita encerramento limpo da fila de mensagens Win32 e libera hooks/timers."""
        self.running = False
        with self._devchange_lock:
            if self._devchange_timer is not None:
                self._devchange_timer.cancel()
                self._devchange_timer = None
        if self._sink_hwnd:
            try:
                user32.PostMessageW(self._sink_hwnd, WM_CLOSE, 0, 0)
            except Exception:
                pass
        if self._pump_tid:
            try:
                user32.PostThreadMessageW(self._pump_tid, WM_QUIT, 0, 0)
            except Exception:
                pass

    def handle_wearing_sensor(self, is_worn: bool) -> None:
        """Acionado quando o sensor infravermelho reporta transição real de presença no ouvido."""
        if self.last_wearing_state is None:
            self.last_wearing_state = is_worn
            return

        if self.last_wearing_state and not is_worn:
            trigger_windows_media_play_pause()
            if self.on_toast:
                self.on_toast("Fone retirado: Mídia pausada", "⏸️")
        elif not self.last_wearing_state and is_worn:
            trigger_windows_media_play_pause()
            if self.on_toast:
                self.on_toast("Fone no ouvido: Mídia retomada", "▶️")

        self.last_wearing_state = is_worn

    def evaluate_process_name(self, proc: str) -> bool:
        """Avalia o executável informado e dispara o combo acústico correspondente se mudou."""
        if not self.auto_profile_enabled or not proc:
            return False
        low = proc.strip().lower()
        if low == self.current_fg_app:
            return False
        self.current_fg_app = low

        with self._rules_lock:
            matched_rule = dict(self._rules_by_exe[low]) if low in self._rules_by_exe else None

        if matched_rule:
            is_gaming = matched_rule.get("spatial_mode") == "esports" or "game" in matched_rule.get("label", "").lower()
            set_process_priority(is_gaming)

            if self.on_apply_automation_rule:
                self.on_apply_automation_rule(matched_rule)
            elif self.on_apply_preset:
                toast_txt = f"{matched_rule['icon']} {matched_rule['label']}: {matched_rule['eq_preset']}!"
                self.on_apply_preset(matched_rule["eq_preset"], toast_txt)
            return True
        else:
            set_process_priority(False)
        return False

    def _evaluate_foreground_hwnd(self, hwnd: Optional[int] = None) -> None:
        if not self.auto_profile_enabled:
            return
        proc = get_process_name_from_hwnd(hwnd)
        if proc:
            self.evaluate_process_name(proc)

    def _schedule_debounced_device_event(self) -> None:
        """
        Coalesce múltiplos eventos `WM_DEVICECHANGE` enviados pelo Windows 11 durante o handshake
        A2DP/HFP ao abrir o estojo dos fones, disparando `on_bluetooth_device_event` uma única vez.
        """
        if not self.on_bluetooth_device_event or not self.running:
            return
        with self._devchange_lock:
            if self._devchange_timer is not None:
                self._devchange_timer.cancel()
            timer = threading.Timer(2.2, self._fire_device_event)
            timer.daemon = True
            self._devchange_timer = timer
            timer.start()

    def _fire_device_event(self) -> None:
        if self.running and self.on_bluetooth_device_event:
            try:
                self.on_bluetooth_device_event()
            except Exception:
                pass

    def _win32_event_pump_worker(self) -> None:
        """
        Thread única bloqueada no kernel via `GetMessageW` (0.0% de CPU):
        - Recebe `WM_HOTKEY` (Ctrl+Shift+A e Ctrl+Shift+E)
        - Recebe `WM_POWERBROADCAST` (Sleep / Hibernate / Resume do Windows 11)
        - Recebe `WM_DEVICECHANGE` (Chegada / Despertar de hardware Bluetooth Zero-Click)
        - Recebe `EVENT_SYSTEM_FOREGROUND` via `SetWinEventHook` sem nenhum loop `time.sleep`!
        """
        self._pump_tid = kernel32.GetCurrentThreadId()
        hinst = kernel32.GetModuleHandleW(None)
        class_name = f"SonySoundConnectPowerSink_{os.getpid()}_{self._pump_tid}"

        def _wnd_proc(hwnd: int, msg: int, wparam: int, lparam: int) -> int:
            if msg == WM_HOTKEY:
                if wparam == HOTKEY_ID_NC and self.on_toggle_nc:
                    threading.Thread(target=self.on_toggle_nc, daemon=True).start()
                elif wparam == HOTKEY_ID_EQ and self.on_cycle_eq:
                    threading.Thread(target=self.on_cycle_eq, daemon=True).start()
                return 0

            if msg == WM_DEVICECHANGE:
                if wparam in (DBT_DEVNODES_CHANGED, DBT_DEVICEARRIVAL):
                    self._schedule_debounced_device_event()
                return 1

            if msg == WM_POWERBROADCAST:
                if wparam == PBT_APMSUSPEND:
                    if self.on_system_suspend:
                        threading.Thread(target=self.on_system_suspend, daemon=True).start()
                elif wparam in (PBT_APMRESUMEAUTOMATIC, PBT_APMRESUMESUSPEND):
                    now = time.monotonic()
                    if now - self._last_resume_ts > 3.0:
                        self._last_resume_ts = now
                        if self.on_system_resume:
                            threading.Thread(target=self.on_system_resume, daemon=True).start()
                return 1

            if msg == WM_CLOSE:
                user32.DestroyWindow(hwnd)
                user32.PostQuitMessage(0)
                return 0

            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        def _win_event_cb(
            h_hook: int,
            event: int,
            hwnd: int,
            id_object: int,
            id_child: int,
            event_thread: int,
            event_time: int,
        ) -> None:
            if event == EVENT_SYSTEM_FOREGROUND and hwnd:
                self._evaluate_foreground_hwnd(hwnd)

        self._wndproc_ref = WNDPROC(_wnd_proc)
        self._winevent_proc_ref = WINEVENTPROC(_win_event_cb)

        wc = WNDCLASSW()
        wc.lpfnWndProc = self._wndproc_ref
        wc.hInstance = hinst
        wc.lpszClassName = class_name
        user32.RegisterClassW(ctypes.byref(wc))

        hwnd = user32.CreateWindowExW(
            WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE,
            class_name,
            "SonySoundConnectSink",
            WS_POPUP,
            0,
            0,
            0,
            0,
            None,
            None,
            hinst,
            None,
        )
        self._sink_hwnd = hwnd

        target_hk_hwnd = hwnd if hwnd else None
        user32.RegisterHotKey(target_hk_hwnd, HOTKEY_ID_NC, MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT, ord("A"))
        user32.RegisterHotKey(target_hk_hwnd, HOTKEY_ID_EQ, MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT, ord("E"))

        hook_handle = user32.SetWinEventHook(
            EVENT_SYSTEM_FOREGROUND,
            EVENT_SYSTEM_FOREGROUND,
            None,
            self._winevent_proc_ref,
            0,
            0,
            WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNPROCESS,
        )

        self._evaluate_foreground_hwnd(None)

        msg = ctypes.wintypes.MSG()
        try:
            while self.running:
                res = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if res <= 0:
                    break
                if msg.message == WM_HOTKEY and not msg.hwnd:
                    if msg.wParam == HOTKEY_ID_NC and self.on_toggle_nc:
                        threading.Thread(target=self.on_toggle_nc, daemon=True).start()
                    elif msg.wParam == HOTKEY_ID_EQ and self.on_cycle_eq:
                        threading.Thread(target=self.on_cycle_eq, daemon=True).start()
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            if hook_handle:
                user32.UnhookWinEvent(hook_handle)
            user32.UnregisterHotKey(target_hk_hwnd, HOTKEY_ID_NC)
            user32.UnregisterHotKey(target_hk_hwnd, HOTKEY_ID_EQ)
            if self._sink_hwnd:
                try:
                    user32.DestroyWindow(self._sink_hwnd)
                except Exception:
                    pass
                self._sink_hwnd = None
