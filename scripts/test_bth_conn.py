import subprocess

# Test 1: AudioEndpoint Present state
ps_audio = """
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Get-PnpDevice -Class AudioEndpoint | Where-Object { $_.FriendlyName -match 'WF-1000' } | Select-Object FriendlyName, Status, Present | ConvertTo-Json
"""
res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_audio], capture_output=True, text=True, encoding="utf-8", errors="replace")
print("AudioEndpoint:")
print(res.stdout)

# Test 2: Windows.Devices.Bluetooth WinRT or Bluetooth battery property
ps_bth = """
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$p = Get-PnpDeviceProperty -InstanceId 'BTHENUM\\DEV_143FA65DDFD5\\7&39D964EC&0&BLUETOOTHDEVICE_143FA65DDFD5' -KeyName '{104EA319-6EE2-4701-BD47-8DDBF425BBE5} 2' -ErrorAction SilentlyContinue
Write-Output "Battery Property: $($p.Data)"
"""
res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_bth], capture_output=True, text=True, encoding="utf-8", errors="replace")
print("Battery PnP:")
print(res.stdout)

# Test 3: Windows.Devices.Bluetooth.BluetoothDevice.FromBluetoothAddressAsync
ps_winrt = """
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
try {
    Add-Type -AssemblyName System.Runtime.WindowsRuntime
    $asTaskGeneric = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' }[0]
    function Await($WinRtTask, $ResultType) {
        $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
        $netTask = $asTask.Invoke($null, @($WinRtTask))
        $netTask.Wait(-1) | Out-Null
        $netTask.Result
    }
    [Windows.Devices.Bluetooth.BluetoothDevice, Windows.Devices.Bluetooth, ContentType = WindowsRuntime] | Out-Null
    $macInt = [Convert]::ToInt64("143FA65DDFD5", 16)
    $devOp = [Windows.Devices.Bluetooth.BluetoothDevice]::FromBluetoothAddressAsync($macInt)
    $dev = Await $devOp ([Windows.Devices.Bluetooth.BluetoothDevice])
    if ($dev) {
        Write-Output "ConnectionStatus: $($dev.ConnectionStatus)"
    } else {
        Write-Output "Device not found"
    }
} catch {
    Write-Output "WinRT Error: $_"
}
"""
res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_winrt], capture_output=True, text=True, encoding="utf-8", errors="replace")
print("WinRT Bluetooth Status:")
print(res.stdout)

