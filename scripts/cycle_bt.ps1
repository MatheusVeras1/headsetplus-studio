Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

[StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
public struct BLUETOOTH_DEVICE_INFO {
    public uint dwSize;
    public ulong Address;
    public uint ulClassofDevice;
    [MarshalAs(UnmanagedType.Bool)] public bool fConnected;
    [MarshalAs(UnmanagedType.Bool)] public bool fRemembered;
    [MarshalAs(UnmanagedType.Bool)] public bool fAuthenticated;
    public SYSTEMTIME stLastSeen;
    public SYSTEMTIME stLastUsed;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 248)] public string szName;
}

[StructLayout(LayoutKind.Sequential)]
public struct SYSTEMTIME {
    public ushort wYear, wMonth, wDayOfWeek, wDay, wHour, wMinute, wSecond, wMilliseconds;
}

public class BtCycle {
    [DllImport("BluetoothAPIs.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    public static extern uint BluetoothGetDeviceInfo(IntPtr hRadio, ref BLUETOOTH_DEVICE_INFO pbtdi);

    [DllImport("BluetoothAPIs.dll", SetLastError = true)]
    public static extern uint BluetoothSetServiceState(IntPtr hRadio, ref BLUETOOTH_DEVICE_INFO pbtdi, ref Guid pGuidService, uint dwServiceFlags);

    public static void SetService(ulong addr, string guidStr, uint flags) {
        BLUETOOTH_DEVICE_INFO bdi = new BLUETOOTH_DEVICE_INFO();
        bdi.dwSize = (uint)Marshal.SizeOf(typeof(BLUETOOTH_DEVICE_INFO));
        bdi.Address = addr;
        BluetoothGetDeviceInfo(IntPtr.Zero, ref bdi);
        Guid g = new Guid(guidStr);
        uint res = BluetoothSetServiceState(IntPtr.Zero, ref bdi, ref g, flags);
        Console.WriteLine(string.Format("Service {0} -> Flags={1} | Res={2}", guidStr, flags, res));
    }
}
"@

$addr = 0x143FA65DDFD5
$services = @(
    "96cc203e-5068-46ad-b32d-e316f5e069ba",
    "0000110e-0000-1000-8000-00805f9b34fb",
    "0000110c-0000-1000-8000-00805f9b34fb",
    "0000110b-0000-1000-8000-00805f9b34fb"
)

Write-Output "--- Disconnecting WF-1000XM3 services cleanly ---"
foreach ($s in $services) {
    [BtCycle]::SetService($addr, $s, 0)
}
Start-Sleep -Seconds 3
Write-Output "--- Reconnecting WF-1000XM3 services cleanly ---"
foreach ($s in $services) {
    [BtCycle]::SetService($addr, $s, 1)
}
Start-Sleep -Seconds 3
