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

public class AudioManager {
    public static void InspectAll() {
        Type t = Type.GetTypeFromCLSID(new Guid("BCDE0395-E52F-467C-8E3D-C4579291692E"));
        IMMDeviceEnumerator enumerator = (IMMDeviceEnumerator)Activator.CreateInstance(t);
        PROPERTYKEY PKEY_Device_FriendlyName = new PROPERTYKEY { fmtid = new Guid("a45c254e-df1c-4efd-8020-67d146a850e0"), pid = 14 };
        PROPERTYKEY PKEY_Disable_SysFx = new PROPERTYKEY { fmtid = new Guid("1da5d803-d492-4edd-8c23-e0c0ffee7f0e"), pid = 5 };

        for (int flow = 0; flow <= 1; flow++) {
            IMMDeviceCollection col;
            enumerator.EnumAudioEndpoints(flow, 0x0F, out col);
            uint count; col.GetCount(out count);
            for (uint i = 0; i < count; i++) {
                IMMDevice dev; col.Item(i, out dev);
                string id; dev.GetId(out id);
                int state; dev.GetState(out state);
                IPropertyStore store; dev.OpenPropertyStore(0, out store);
                PROPVARIANT pv; store.GetValue(ref PKEY_Device_FriendlyName, out pv);
                string name = pv.vt == 31 ? Marshal.PtrToStringUni(pv.p) : "";
                PROPVARIANT pvFx; store.GetValue(ref PKEY_Disable_SysFx, out pvFx);
                long sysFx = pvFx.p.ToInt64();
                if (name.Contains("WF-1000XM3") || state == 1) {
                    Console.WriteLine((flow == 0 ? "[Render]  " : "[Capture] ") + "State=" + state + " | SysFxOff=" + sysFx + " | " + name + " | " + id);
                }
            }
        }
    }
}
"@
[AudioManager]::InspectAll()
