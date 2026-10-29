# -*- coding: utf-8 -*-
"""
Sony Sound Connect PC — Utilitários de Integração de Baixo Nível Win32 & DWM
Created by Matheus Veras • Licença: Source-Available Proprietary (Ver LICENSE.md)

Responsabilidades:
- Garantia de Instância Única via Mutex Global Nomeado Win32.
- Consulta de cor de destaque oficial do Windows 11 no Registro DWM.
- Configuração de inicialização automática no Registro do Windows.
- Detecção nativa do idioma do sistema operacional (Win32 GetUserDefaultUILanguage).
- Injeção de ícone oficial 2K (.ico) na janela e na barra de tarefas Win32.
"""

import ctypes
import locale
import os
import sys
import winreg
from typing import Any, Dict, List, Optional

_single_instance_mutex = None


def acquire_single_instance_lock() -> bool:
    """
    Garante instância única do aplicativo no Windows 11 via Mutex global nomeado.
    Caso outra instância já esteja em execução, restaura a janela existente e encerra.
    """
    global _single_instance_mutex
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        _single_instance_mutex = kernel32.CreateMutexW(
            None, False, "Global\\HeadsetPlusStudio_SingleInstance_Mutex"
        )
        if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            hwnd = user32.FindWindowW(None, "HeadsetPlus Studio") or user32.FindWindowW(None, "Sony | G HUB Studio — WF-1000XM3 Edition")
            if hwnd:
                user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                user32.SetForegroundWindow(hwnd)
            return False
        return True
    except Exception:
        return True


def release_single_instance_lock() -> None:
    """Libera o handle do Mutex Win32 na saída para permitir reinicializações imediatas sem bloqueio."""
    global _single_instance_mutex
    if _single_instance_mutex is not None:
        try:
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.CloseHandle(_single_instance_mutex)
        except Exception:
            pass
        _single_instance_mutex = None


def query_windows_accent_color() -> Dict[str, Any]:
    """
    Lê a cor de destaque oficial do Windows 11 via Registro do DWM
    (HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\DWM)
    e retorna o valor hexadecimal (#RRGGBB) compatível com o tema CSS da aplicação.
    """
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\DWM")
        val, _ = winreg.QueryValueEx(key, "AccentColor")
        winreg.CloseKey(key)
        r = val & 0xFF
        g = (val >> 8) & 0xFF
        b = (val >> 16) & 0xFF
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        return {"success": True, "accent_hex": hex_color}
    except Exception as e:
        return {"success": False, "accent_hex": "#00e5ff", "error": str(e)}


def set_windows_run_at_startup(enabled: bool) -> bool:
    """Configura inicialização automática do driver no Windows 11 (HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run)."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE,
        )
        app_name = "HeadsetPlusStudio"
        if enabled:
            pyw_path = os.path.abspath(sys.argv[0])
            cmd = f'"{sys.executable}" "{pyw_path}"'
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, cmd)
        else:
            for old_n in ["HeadsetPlusStudio", "SonySoundConnectPC"]:
                try:
                    winreg.DeleteValue(key, old_n)
                except FileNotFoundError:
                    pass
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def get_windows_run_at_startup() -> bool:
    """Verifica se o aplicativo está configurado para iniciar com o Windows 11."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_QUERY_VALUE,
        )
        for app_name in ["HeadsetPlusStudio", "SonySoundConnectPC"]:
            try:
                val, _ = winreg.QueryValueEx(key, app_name)
                winreg.CloseKey(key)
                return bool(val)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return False
    except Exception:
        return False


def detect_system_language() -> str:
    """
    Detecta o idioma nativo de exibição do Windows e mapeia para os idiomas suportados pela suíte.
    Retorna um dos códigos oficiais: 'pt-BR', 'en-US', 'ja-JP', 'es-ES', 'de-DE', 'zh-CN', 'fr-FR'.
    Caso o idioma do sistema não esteja entre os suportados, retorna 'en-US' como padrão universal seguro.
    """
    try:
        if hasattr(ctypes, "windll") and hasattr(ctypes.windll, "kernel32"):
            lcid = ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF
            lang_map = {
                0x16: "pt-BR",
                0x09: "en-US",
                0x11: "ja-JP",
                0x0A: "es-ES",
                0x07: "de-DE",
                0x04: "zh-CN",
                0x0C: "fr-FR",
            }
            if lcid in lang_map:
                return lang_map[lcid]
    except Exception:
        pass

    try:
        loc = (locale.getdefaultlocale()[0] or "").lower()
        if "pt" in loc:
            return "pt-BR"
        elif "ja" in loc:
            return "ja-JP"
        elif "es" in loc:
            return "es-ES"
        elif "de" in loc:
            return "de-DE"
        elif "zh" in loc:
            return "zh-CN"
        elif "fr" in loc:
            return "fr-FR"
    except Exception:
        pass

    return "en-US"


def apply_win32_window_icon(window_title: Optional[str] = None) -> None:
    """Aplica o ícone .ico oficial 2K na barra de título e barra de tarefas do Windows 11."""
    from app.config import ICON_ICO_PATH

    if not os.path.exists(ICON_ICO_PATH):
        return
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        curr_pid = kernel32.GetCurrentProcessId()

        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x00000010
        WM_SETICON = 0x0080
        ICON_SMALL = 0
        ICON_BIG = 1
        GCLP_HICON = -14
        GCLP_HICONSM = -34

        hicon_big = user32.LoadImageW(0, ICON_ICO_PATH, IMAGE_ICON, 48, 48, LR_LOADFROMFILE)
        hicon_sml = user32.LoadImageW(0, ICON_ICO_PATH, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)

        hwnds: List[int] = []

        def enum_cb(hwnd: int, lparam: int) -> bool:
            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value == curr_pid:
                hwnds.append(hwnd)
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)

        if window_title:
            h = user32.FindWindowW(None, window_title)
            if h and h not in hwnds:
                hwnds.append(h)

        for hwnd in hwnds:
            if hicon_big:
                user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_big)
                try:
                    user32.SetClassLongPtrW(hwnd, GCLP_HICON, hicon_big)
                except Exception:
                    pass
            if hicon_sml:
                user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_sml)
                try:
                    user32.SetClassLongPtrW(hwnd, GCLP_HICONSM, hicon_sml)
                except Exception:
                    pass
    except Exception:
        pass

