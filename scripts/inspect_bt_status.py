import subprocess
import json

ps_script = """
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$devices = Get-PnpDevice | Where-Object { $_.FriendlyName -match 'WF-1000' -or $_.FriendlyName -match 'Sony' }
$res = foreach ($d in $devices) {
    [PSCustomObject]@{
        FriendlyName = $d.FriendlyName
        InstanceId = $d.InstanceId
        Class = $d.Class
        Status = $d.Status
        Present = $d.Present
    }
}
$res | ConvertTo-Json
"""

res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True, encoding="utf-8", errors="replace")
print("PnP Devices:")
print(res.stdout)
