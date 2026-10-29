@echo off
cd /d "%~dp0"
if exist "dist\HeadsetPlusStudio.exe" (
    start "" "dist\HeadsetPlusStudio.exe" %*
) else (
    powershell -NoProfile -WindowStyle Hidden -Command "Get-CimInstance Win32_Process -Filter \"Name='pythonw.exe' AND CommandLine LIKE '%headsetplus_studio%'\" | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
    start "" "C:\Users\mathe\AppData\Local\Programs\Python\Python310\pythonw.exe" "headsetplus_studio.pyw" %*
)
