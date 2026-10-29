Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

[Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator {
    int EnumAudioEndpoints(int dataFlow, int dwStateMask, out IMMDeviceCollection ppDevices);
    int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice ppEndpoint);
}

[Guid("0BD7A1BE-7A1A-44DB-8397-CC5392387B5E"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceCollection {
    int GetCount(out uint pcDevices);
    int Item(uint nDevice, out IMMDevice ppDevice);
}

[Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice {
    int Activate(ref Guid iid, int dwClsCtx, IntPtr pActivationParams, out IntPtr ppInterface);
    int OpenPropertyStore(int stgmAccess, out IPropertyStore ppProperties);
    int GetId([MarshalAs(UnmanagedType.LPWStr)] out string ppstrId);
    int GetState(out int pdwState);
}

[Guid("886d8eeb-8cf2-4446-8d02-cdba1dbdcf99"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IPropertyStore {
    int GetCount(out uint cProps);
    int GetAt(uint iProp, out PROPERTYKEY pkey);
    int GetValue(ref PROPERTYKEY key, out PROPVARIANT pv);
}

[Guid("f8679f50-850a-41cf-9c72-430f290290c8"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IPolicyConfig {
    int GetMixFormat([MarshalAs(UnmanagedType.LPWStr)] string pszDeviceName, out IntPtr ppFormat);
    int GetDeviceFormat([MarshalAs(UnmanagedType.LPWStr)] string pszDeviceName, int bDefault, out IntPtr ppFormat);
    int ResetDeviceFormat([MarshalAs(UnmanagedType.LPWStr)] string pszDeviceName);
    int SetDeviceFormat([MarshalAs(UnmanagedType.LPWStr)] string pszDeviceName, IntPtr pEndpointFormat, IntPtr MixFormat);
    int GetProcessingPeriod([MarshalAs(UnmanagedType.LPWStr)] string pszDeviceName, int bDefault, IntPtr pmftDefaultPeriod, IntPtr pmftMinimumPeriod);
    int SetProcessingPeriod([MarshalAs(UnmanagedType.LPWStr)] string pszDeviceName, IntPtr pmftPeriod);
    int GetShareMode([MarshalAs(UnmanagedType.LPWStr)] string pszDeviceName, IntPtr pMode);
    int SetShareMode([MarshalAs(UnmanagedType.LPWStr)] string pszDeviceName, IntPtr mode);
    int GetPropertyValue([MarshalAs(UnmanagedType.LPWStr)] string pszDeviceName, int bFxStore, ref PROPERTYKEY key, out PROPVARIANT pv);
    int SetPropertyValue([MarshalAs(UnmanagedType.LPWStr)] string pszDeviceName, int bFxStore, ref PROPERTYKEY key, ref PROPVARIANT pv);
    int SetDefaultEndpoint([MarshalAs(UnmanagedType.LPWStr)] string pszDeviceName, int role);
    int SetEndpointVisibility([MarshalAs(UnmanagedType.LPWStr)] string pszDeviceName, int bVisible);
}

[StructLayout(LayoutKind.Sequential)]
public struct PROPERTYKEY {
    public Guid fmtid;
    public uint pid;
}

[StructLayout(LayoutKind.Sequential)]
public struct PROPVARIANT {
    public ushort vt;
    public ushort r1, r2, r3;
    public IntPtr p;
    public int p2;
}

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

public class AudioOptimizer {
    [DllImport("BluetoothAPIs.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    public static extern uint BluetoothGetDeviceInfo(IntPtr hRadio, ref BLUETOOTH_DEVICE_INFO pbtdi);

    [DllImport("BluetoothAPIs.dll", SetLastError = true)]
    public static extern uint BluetoothSetServiceState(IntPtr hRadio, ref BLUETOOTH_DEVICE_INFO pbtdi, ref Guid pGuidService, uint dwServiceFlags);

    public static void SetBtService(ulong addr, string guidStr, uint flags) {
        BLUETOOTH_DEVICE_INFO bdi = new BLUETOOTH_DEVICE_INFO();
        bdi.dwSize = (uint)Marshal.SizeOf(typeof(BLUETOOTH_DEVICE_INFO));
        bdi.Address = addr;
        BluetoothGetDeviceInfo(IntPtr.Zero, ref bdi);
        Guid g = new Guid(guidStr);
        BluetoothSetServiceState(IntPtr.Zero, ref bdi, ref g, flags);
    }

    public static void ApplyOptimizations() {
        ulong btAddr = 0x143FA65DDFD5;
        // Disable Hands-Free HFP and unused RFCOMM services at the Bluetooth radio level
        SetBtService(btAddr, "0000111e-0000-1000-8000-00805f9b34fb", 0);
        SetBtService(btAddr, "00000000-deca-fade-deca-deafdecacaff", 0);
        SetBtService(btAddr, "8901dfa8-5c7e-4d8f-9f0c-c2b70683f5f0", 0);
        SetBtService(btAddr, "8a482a08-5507-42ac-b673-a88df48b3fc7", 0);
        SetBtService(btAddr, "b9b213ce-eeab-49e4-8fd9-aa478ed1b26b", 0);

        Type tPolicy = Type.GetTypeFromCLSID(new Guid("870af99c-171d-4f9e-af0d-e63df40c2bc9"));
        IPolicyConfig policy = (IPolicyConfig)Activator.CreateInstance(tPolicy);

        string wfStereoId = "{0.0.0.00000000}.{060db25e-029f-4123-8880-792277d03ac8}";
        string wfHandsFreeRenderId = "{0.0.0.00000000}.{f23f1652-456e-4e9f-8d95-a8659b474763}";
        string wfHandsFreeCaptureId = "{0.0.1.00000000}.{f8615506-60ef-4fd8-adb9-f87d006245c0}";
        string internalMicId = "{0.0.1.00000000}.{d10ceafc-de15-4155-967a-253fa1f410fd}";

        policy.SetEndpointVisibility(wfHandsFreeRenderId, 0);
        policy.SetEndpointVisibility(wfHandsFreeCaptureId, 0);
        policy.SetEndpointVisibility(wfStereoId, 1);

        for (int role = 0; role <= 2; role++) {
            policy.SetDefaultEndpoint(wfStereoId, role);
            policy.SetDefaultEndpoint(internalMicId, role);
        }

        PROPERTYKEY PKEY_Disable_SysFx = new PROPERTYKEY { fmtid = new Guid("1da5d803-d492-4edd-8c23-e0c0ffee7f0e"), pid = 5 };
        PROPVARIANT pvDisable = new PROPVARIANT { vt = 19, p = new IntPtr(1) };
        policy.SetPropertyValue(wfStereoId, 0, ref PKEY_Disable_SysFx, ref pvDisable);
        policy.SetPropertyValue(wfStereoId, 1, ref PKEY_Disable_SysFx, ref pvDisable);
    }
}
"@
[AudioOptimizer]::ApplyOptimizations()
