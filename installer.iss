; Script de Instalação Oficial Inno Setup — Sony Sound Connect PC
; Created by Matheus Veras • Gratuito e Open-Source

[Setup]
AppId={{A8C346B8-22F1-4F43-85D7-9C9D176EF8D2}}
AppName=Sony Sound Connect PC
AppVersion=1.0.0
AppPublisher=Matheus Veras
DefaultDirName={autopf}\SonySoundConnectPC
DefaultGroupName=Sony Sound Connect PC
OutputDir=dist
OutputBaseFilename=SonySoundConnect-v1.0.0-Setup
SetupIconFile=assets\app_icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\SonySoundConnect.exe

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "startupicon"; Description: "Iniciar automaticamente com o Windows"; GroupDescription: "Opções Adicionais:"

[Files]
Source: "dist\SonySoundConnect.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "fix_windows_audio.ps1"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Sony Sound Connect PC"; Filename: "{app}\SonySoundConnect.exe"
Name: "{group}\Desinstalar Sony Sound Connect PC"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Sony Sound Connect PC"; Filename: "{app}\SonySoundConnect.exe"; Tasks: desktopicon
Name: "{autostartup}\Sony Sound Connect PC"; Filename: "{app}\SonySoundConnect.exe"; Tasks: startupicon

[Run]
Filename: "{app}\SonySoundConnect.exe"; Description: "{cm:LaunchProgram,Sony Sound Connect PC}"; Flags: nowait postinstall skipifsilent
