; Script de Instalação Oficial Inno Setup — HeadsetPlus Studio
; Created by Matheus Veras • Gratuito e Open-Source

[Setup]
AppId={{A8C346B8-22F1-4F43-85D7-9C9D176EF8D2}}
AppName=HeadsetPlus Studio
AppVersion=1.0.0
AppPublisher=Matheus Veras
DefaultDirName={autopf}\HeadsetPlusStudio
DefaultGroupName=HeadsetPlus Studio
OutputDir=dist
OutputBaseFilename=HeadsetPlus-Studio-v1.0.0-Setup
SetupIconFile=assets\app_icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\HeadsetPlusStudio.exe

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "startupicon"; Description: "Iniciar automaticamente com o Windows"; GroupDescription: "Opções Adicionais:"

[Files]
Source: "dist\HeadsetPlusStudio.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "fix_windows_audio.ps1"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\HeadsetPlus Studio"; Filename: "{app}\HeadsetPlusStudio.exe"
Name: "{group}\Desinstalar HeadsetPlus Studio"; Filename: "{uninstallexe}"
Name: "{autodesktop}\HeadsetPlus Studio"; Filename: "{app}\HeadsetPlusStudio.exe"; Tasks: desktopicon
Name: "{autostartup}\HeadsetPlus Studio"; Filename: "{app}\HeadsetPlusStudio.exe"; Tasks: startupicon

[Run]
Filename: "{app}\HeadsetPlusStudio.exe"; Description: "{cm:LaunchProgram,HeadsetPlus Studio}"; Flags: nowait postinstall skipifsilent
