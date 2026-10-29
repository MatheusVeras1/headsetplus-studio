@echo off
cd /d "%~dp0"
powershell -NoProfile -WindowStyle Hidden -Command "Get-CimInstance Win32_Process -Filter \"Name='pythonw.exe' AND CommandLine LIKE '%sony_sound_connect_pc%'\" | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
start "" "C:\Users\mathe\AppData\Local\Programs\Python\Python310\pythonw.exe" "C:\Users\mathe\Documents\sony headsetPlus\sony_sound_connect_pc.pyw" %*
