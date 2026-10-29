import ctypes
from ctypes import wintypes

class BLUETOOTH_ADDRESS(ctypes.Structure):
    _fields_ = [("ullLong", ctypes.c_ulonglong)]

class SYSTEMTIME(ctypes.Structure):
    _fields_ = [
        ("wYear", wintypes.WORD),
        ("wMonth", wintypes.WORD),
        ("wDayOfWeek", wintypes.WORD),
        ("wDay", wintypes.WORD),
        ("wHour", wintypes.WORD),
        ("wMinute", wintypes.WORD),
        ("wSecond", wintypes.WORD),
        ("wMilliseconds", wintypes.WORD),
    ]

class BLUETOOTH_DEVICE_INFO(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("Address", BLUETOOTH_ADDRESS),
        ("ulClassofDevice", wintypes.ULONG),
        ("fConnected", wintypes.BOOL),
        ("fRemembered", wintypes.BOOL),
        ("fAuthenticated", wintypes.BOOL),
        ("stLastSeen", SYSTEMTIME),
        ("stLastUsed", SYSTEMTIME),
        ("szName", wintypes.WCHAR * 248),
    ]

bth = ctypes.windll.BluetoothApis

# MAC 14:3F:A6:5D:DF:D5 -> integer
mac_str = "14:3F:A6:5D:DF:D5"
raw_mac = int(mac_str.replace(":", ""), 16)

info = BLUETOOTH_DEVICE_INFO()
info.dwSize = ctypes.sizeof(BLUETOOTH_DEVICE_INFO)
info.Address.ullLong = raw_mac

ret = bth.BluetoothGetDeviceInfo(None, ctypes.byref(info))
print("BluetoothGetDeviceInfo return code:", ret)
if ret == 0:
    print(f"Device Name: {info.szName}")
    print(f"fConnected: {bool(info.fConnected)}")
    print(f"fRemembered: {bool(info.fRemembered)}")
    print(f"fAuthenticated: {bool(info.fAuthenticated)}")
else:
    print("Error getting device info:", ctypes.GetLastError())

