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

public class BtServiceFix {
    [DllImport("BluetoothAPIs.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    public static extern uint BluetoothGetDeviceInfo(IntPtr hRadio, ref BLUETOOTH_DEVICE_INFO pbtdi);

    [DllImport("BluetoothAPIs.dll", SetLastError = true)]
    public static extern uint BluetoothSetServiceState(IntPtr hRadio, ref BLUETOOTH_DEVICE_INFO pbtdi, ref Guid pGuidService, uint dwServiceFlags);

    public static void SetService(ulong addr, string guidStr, uint flags, string label) {
        BLUETOOTH_DEVICE_INFO bdi = new BLUETOOTH_DEVICE_INFO();
        bdi.dwSize = (uint)Marshal.SizeOf(typeof(BLUETOOTH_DEVICE_INFO));
        bdi.Address = addr;
        BluetoothGetDeviceInfo(IntPtr.Zero, ref bdi);
        Guid g = new Guid(guidStr);
        uint res = BluetoothSetServiceState(IntPtr.Zero, ref bdi, ref g, flags);
        Console.WriteLine(string.Format("{0} ({1}) -> Flags={2} | Result={3}", label, guidStr, flags, res));
    }
}
"@

$addr = 0x143FA65DDFD5
# 1. Disable Hands-Free Profile (HFP) at the Bluetooth radio/service level!
[BtServiceFix]::SetService($addr, "0000111e-0000-1000-8000-00805f9b34fb", 0, "Disable Hands-Free HFP")
# 2. Disable unused extra RFCOMM services (IAPSERVER, Airoha_APP, Wireless TCX, Serial MC)
[BtServiceFix]::SetService($addr, "00000000-deca-fade-deca-deafdecacaff", 0, "Disable Apple iAP")
[BtServiceFix]::SetService($addr, "8901dfa8-5c7e-4d8f-9f0c-c2b70683f5f0", 0, "Disable Airoha_APP")
[BtServiceFix]::SetService($addr, "8a482a08-5507-42ac-b673-a88df48b3fc7", 0, "Disable Wireless TCX")
[BtServiceFix]::SetService($addr, "b9b213ce-eeab-49e4-8fd9-aa478ed1b26b", 0, "Disable Serial MC")
# 3. Cycle Serial HPC (Sony App Control) to clear wedged RFCOMM socket
[BtServiceFix]::SetService($addr, "96cc203e-5068-46ad-b32d-e316f5e069ba", 0, "Reset Serial HPC (Disable)")
Start-Sleep -Milliseconds 800
[BtServiceFix]::SetService($addr, "96cc203e-5068-46ad-b32d-e316f5e069ba", 1, "Reset Serial HPC (Enable)")
