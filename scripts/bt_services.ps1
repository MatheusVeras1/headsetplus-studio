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

public class BtHelper {
    [DllImport("BluetoothAPIs.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    public static extern uint BluetoothGetDeviceInfo(IntPtr hRadio, ref BLUETOOTH_DEVICE_INFO pbtdi);

    [DllImport("BluetoothAPIs.dll", SetLastError = true)]
    public static extern uint BluetoothEnumerateInstalledServices(IntPtr hRadio, ref BLUETOOTH_DEVICE_INFO pbtdi, ref uint pcServiceInout, [Out] Guid[] pGuidServices);

    [DllImport("BluetoothAPIs.dll", SetLastError = true)]
    public static extern uint BluetoothSetServiceState(IntPtr hRadio, ref BLUETOOTH_DEVICE_INFO pbtdi, ref Guid pGuidService, uint dwServiceFlags);

    public static void InspectDevice(ulong addr) {
        BLUETOOTH_DEVICE_INFO bdi = new BLUETOOTH_DEVICE_INFO();
        bdi.dwSize = (uint)Marshal.SizeOf(typeof(BLUETOOTH_DEVICE_INFO));
        bdi.Address = addr;
        uint res = BluetoothGetDeviceInfo(IntPtr.Zero, ref bdi);
        Console.WriteLine(string.Format("Device: {0} (0x{1:X12}) | Connected={2} | Remembered={3} | Res={4}", bdi.szName, addr, bdi.fConnected, bdi.fRemembered, res));

        uint count = 32;
        Guid[] guids = new Guid[count];
        uint res2 = BluetoothEnumerateInstalledServices(IntPtr.Zero, ref bdi, ref count, guids);
        Console.WriteLine("  Installed Services (" + count + "):");
        for (int i = 0; i < count; i++) {
            Console.WriteLine("    - " + guids[i]);
        }
    }
}
"@
[BtHelper]::InspectDevice(0x143FA65DDFD5)
[BtHelper]::InspectDevice(0x3C0A7AB1798D)
