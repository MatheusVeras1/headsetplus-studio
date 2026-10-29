# -*- coding: utf-8 -*-
"""
Script de Empacotamento de Releases (Portable ZIP & Inno Setup Builder)
Created by Matheus Veras • Licença: Source-Available Proprietary (Ver LICENSE.md)

Responsabilidades:
- Gera o pacote ZIP portátil autônomo (SonySoundConnect-Portable-v1.0.0.zip).
- Gera o arquivo de configuração de instalador profissional Inno Setup (installer.iss).
- 100% gratuito, sem depender de nenhuma assinatura ou licença paga.
"""

import os
import sys
import zipfile

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(BASE_DIR, "dist")
EXE_PATH = os.path.join(DIST_DIR, "SonySoundConnect.exe")
VERSION = "1.0.0"


def generate_portable_zip() -> str:
    """Gera o arquivo ZIP portátil pronto para distribuição no GitHub Releases."""
    if not os.path.exists(EXE_PATH):
        print("❌ Executável dist/SonySoundConnect.exe não encontrado! Execute scripts/build_standalone_exe.py primeiro.")
        return ""

    zip_filename = f"SonySoundConnect-v{VERSION}-Windows-Portable.zip"
    zip_path = os.path.join(DIST_DIR, zip_filename)

    print(f"📦 Criando pacote portátil: {zip_filename}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(EXE_PATH, arcname="SonySoundConnect.exe")
        for extra in ["LICENSE.md", "fix_windows_audio.ps1"]:
            extra_path = os.path.join(BASE_DIR, extra)
            if os.path.exists(extra_path):
                zf.write(extra_path, arcname=extra)

    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"  ✓ ZIP Portátil gerado com sucesso: {size_mb:.2f} MB")
    return zip_path


def generate_inno_setup_script() -> str:
    """Gera o script installer.iss para compilação com Inno Setup (100% gratuito e open-source)."""
    iss_path = os.path.join(BASE_DIR, "installer.iss")
    content = f"""; Script de Instalação Oficial Inno Setup — Sony Sound Connect PC
; Created by Matheus Veras • Gratuito e Open-Source

[Setup]
AppId={{{{A8C346B8-22F1-4F43-85D7-9C9D176EF8D2}}}}
AppName=Sony Sound Connect PC
AppVersion={VERSION}
AppPublisher=Matheus Veras
DefaultDirName={{autopf}}\\SonySoundConnectPC
DefaultGroupName=Sony Sound Connect PC
OutputDir=dist
OutputBaseFilename=SonySoundConnect-v{VERSION}-Setup
SetupIconFile=assets\\app_icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
UninstallDisplayIcon={{app}}\\SonySoundConnect.exe

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"
Name: "startupicon"; Description: "Iniciar automaticamente com o Windows"; GroupDescription: "Opções Adicionais:"

[Files]
Source: "dist\\SonySoundConnect.exe"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "LICENSE.md"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "fix_windows_audio.ps1"; DestDir: "{{app}}"; Flags: ignoreversion

[Icons]
Name: "{{group}}\\Sony Sound Connect PC"; Filename: "{{app}}\\SonySoundConnect.exe"
Name: "{{group}}\\Desinstalar Sony Sound Connect PC"; Filename: "{{uninstallexe}}"
Name: "{{autodesktop}}\\Sony Sound Connect PC"; Filename: "{{app}}\\SonySoundConnect.exe"; Tasks: desktopicon
Name: "{{autostartup}}\\Sony Sound Connect PC"; Filename: "{{app}}\\SonySoundConnect.exe"; Tasks: startupicon

[Run]
Filename: "{{app}}\\SonySoundConnect.exe"; Description: "{{cm:LaunchProgram,Sony Sound Connect PC}}"; Flags: nowait postinstall skipifsilent
"""
    with open(iss_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✓ Script de instalador Inno Setup gerado: installer.iss")
    return iss_path


if __name__ == "__main__":
    print("=" * 80)
    print("  SONY SOUND CONNECT PC — EMPACOTADOR DE RELEASES PARA GITHUB")
    print("  Created by Matheus Veras • 100% Gratuito (Sem Assinaturas Pagas)")
    print("=" * 80)
    generate_portable_zip()
    generate_inno_setup_script()
    print("=" * 80)

