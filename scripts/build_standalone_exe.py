# -*- coding: utf-8 -*-
"""
Script de Compilação & Empacotamento Executável (SonySoundConnect.exe)
Created by Matheus Veras • Licença: Source-Available Proprietary (Ver LICENSE.md)

Gera um executável único (.exe) nativo para Windows 11 utilizando PyInstaller:
- Modo Standalone (--onefile) e Silencioso sem console (--noconsole).
- Inclusão de todos os recursos (assets 3D, UI HTML/CSS/JS, presets AutoEq, scripts de áudio e licença).
- Metadados oficiais e ícone 2K embutido.
"""

import os
import shutil
import subprocess
import sys
import time

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRY_POINT = os.path.join(BASE_DIR, "headsetplus_studio.pyw")
ICON_PATH = os.path.join(BASE_DIR, "assets", "app_icon.ico")
OUTPUT_NAME = "HeadsetPlusStudio"


def ensure_pyinstaller_installed() -> None:
    """Garante que o PyInstaller está disponível no ambiente."""
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("📦 PyInstaller não encontrado. Instalando automaticamente...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller>=6.0.0"])


def clean_previous_builds() -> None:
    """Limpa diretórios temporários de compilações anteriores para garantir build limpa."""
    for folder in ["build", "dist"]:
        path = os.path.join(BASE_DIR, folder)
        if os.path.exists(path):
            print(f"🧹 Limpando diretório anterior: {folder}/")
            try:
                shutil.rmtree(path)
            except Exception as e:
                print(f"  ⚠️ Aviso ao limpar {folder}: {e}")


def build_executable() -> bool:
    """Executa o empacotamento completo do SonySoundConnect.exe."""
    ensure_pyinstaller_installed()
    clean_previous_builds()

    print("=" * 80)
    print("  HEADSETPLUS STUDIO — BUILD DE EXECUTÁVEL STANDALONE")
    print("  Created by Matheus Veras • Windows 11 Single-File Binary Builder")
    print("=" * 80)

    start_time = time.time()

    # Monta separador de add-data para Windows (';')
    sep = ";"

    data_files = [
        ("assets", "assets"),
        ("ui", "ui"),
        ("ui_ghub.html", "."),
        ("apo_dsp", "apo_dsp"),
        ("fix_windows_audio.ps1", "."),
        ("LICENSE.md", "."),
    ]

    pyinstaller_args = [
        ENTRY_POINT,
        "--name", OUTPUT_NAME,
        "--onefile",
        "--noconsole",
        "--clean",
    ]

    if os.path.exists(ICON_PATH):
        pyinstaller_args.extend(["--icon", ICON_PATH])

    for src, dst in data_files:
        src_path = os.path.join(BASE_DIR, src)
        if os.path.exists(src_path):
            pyinstaller_args.extend(["--add-data", f"{src_path}{sep}{dst}"])

    hidden_imports = [
        "webview",
        "webview.platforms.winforms",
        "pystray",
        "PIL",
        "app",
        "app.config",
        "app.win32_utils",
        "app.tray_manager",
        "app.rpc_bridge",
        "app.controller",
        "core",
        "core.drivers",
        "core.device_detector",
        "core.autoeq_database",
        "core.hearing_safety",
        "core.ios_desktop_overlay",
        "core.system_integration",
        "core.windows_apo_engine",
    ]

    for hi in hidden_imports:
        pyinstaller_args.extend(["--hidden-import", hi])

    print(f"🚀 Iniciando compilação do executável ({OUTPUT_NAME}.exe)...")
    import PyInstaller.__main__
    try:
        PyInstaller.__main__.run(pyinstaller_args)
    except SystemExit as e:
        if e.code != 0:
            print(f"❌ Falha na compilação do PyInstaller com código: {e.code}")
            return False

    elapsed = time.time() - start_time
    exe_path = os.path.join(BASE_DIR, "dist", f"{OUTPUT_NAME}.exe")

    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print("\n" + "=" * 80)
        print(f"  🎉 SUCESSO! Executável gerado com perfeição!")
        print(f"  📁 Arquivo: {exe_path}")
        print(f"  📊 Tamanho: {size_mb:.2f} MB")
        print(f"  ⏱️  Tempo total de compilação: {elapsed:.2f}s")
        print("=" * 80)
        return True
    else:
        print(f"❌ Erro: Arquivo executável não encontrado em {exe_path}")
        return False


if __name__ == "__main__":
    success = build_executable()
    sys.exit(0 if success else 1)
