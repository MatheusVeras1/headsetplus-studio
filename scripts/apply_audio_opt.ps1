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

public class AudioOptimizer {
    public static void ApplyOptimizations() {
        Type tEnum = Type.GetTypeFromCLSID(new Guid("BCDE0395-E52F-467C-8E3D-C4579291692E"));
        IMMDeviceEnumerator enumerator = (IMMDeviceEnumerator)Activator.CreateInstance(tEnum);

        Type tPolicy = Type.GetTypeFromCLSID(new Guid("870af99c-171d-4f9e-af0d-e63df40c2bc9"));
        IPolicyConfig policy = (IPolicyConfig)Activator.CreateInstance(tPolicy);

        string wfStereoId = "{0.0.0.00000000}.{060db25e-029f-4123-8880-792277d03ac8}";
        string wfHandsFreeRenderId = "{0.0.0.00000000}.{f23f1652-456e-4e9f-8d95-a8659b474763}";
        string wfHandsFreeCaptureId = "{0.0.1.00000000}.{f8615506-60ef-4fd8-adb9-f87d006245c0}";
        string internalMicId = "{0.0.1.00000000}.{d10ceafc-de15-4155-967a-253fa1f410fd}";

        // 1. Disable Hands-Free Render & Capture endpoints
        int hr1 = policy.SetEndpointVisibility(wfHandsFreeRenderId, 0);
        int hr2 = policy.SetEndpointVisibility(wfHandsFreeCaptureId, 0);
        Console.WriteLine("1. Disable Hands-Free Render/Capture: HR1=" + hr1 + ", HR2=" + hr2);

        // 2. Ensure WF-1000XM3 Stereo is enabled and set as Default for Console (0), Multimedia (1), and Communications (2)
        policy.SetEndpointVisibility(wfStereoId, 1);
        for (int role = 0; role <= 2; role++) {
            policy.SetDefaultEndpoint(wfStereoId, role);
            policy.SetDefaultEndpoint(internalMicId, role);
        }
        Console.WriteLine("2. Set WF-1000XM3 Stereo as Default Output (Console, Multimedia, Communications) and Internal Mic as Default Input.");

        // 3. Disable Audio Enhancements (SysFx = 1) on WF-1000XM3 Stereo to eliminate extra DSP latency
        PROPERTYKEY PKEY_Disable_SysFx = new PROPERTYKEY { fmtid = new Guid("1da5d803-d492-4edd-8c23-e0c0ffee7f0e"), pid = 5 };
        PROPVARIANT pvDisable = new PROPVARIANT { vt = 19, p = new IntPtr(1) }; // VT_UI4 = 19, value = 1
        int hrFx0 = policy.SetPropertyValue(wfStereoId, 0, ref PKEY_Disable_SysFx, ref pvDisable);
        int hrFx1 = policy.SetPropertyValue(wfStereoId, 1, ref PKEY_Disable_SysFx, ref pvDisable);
        Console.WriteLine("3. Disable Audio Enhancements (SysFx): HR_Endpoint=" + hrFx0 + ", HR_FxStore=" + hrFx1);

        // Verify current state
        IMMDevice dev;
        for (int role = 0; role <= 2; role++) {
            enumerator.GetDefaultAudioEndpoint(0, role, out dev);
            string id; dev.GetId(out id);
            Console.WriteLine("   Verified Default Render Role " + role + ": " + id);
        }
        for (int role = 0; role <= 2; role++) {
            enumerator.GetDefaultAudioEndpoint(1, role, out dev);
            string id; dev.GetId(out id);
            Console.WriteLine("   Verified Default Capture Role " + role + ": " + id);
        }
    }
}
"@
[AudioOptimizer]::ApplyOptimizations()
