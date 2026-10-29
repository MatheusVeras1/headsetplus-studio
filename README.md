# 🎧 Sony Sound Connect PC — G HUB Studio Edition

> **Language / Idioma:** 🇺🇸 **English** | 🇧🇷 [Português (Brasil)](README.pt-BR.md)

[![Windows 11](https://img.shields.io/badge/Windows%2011-Compatible-0078D4?style=for-the-badge&logo=windows11&logoColor=white)](https://microsoft.com)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Equalizer APO](https://img.shields.io/badge/Equalizer%20APO-Integrated-brightgreen?style=for-the-badge)](https://sourceforge.net/projects/equalizerapo/)
[![CI Quality Gate](https://img.shields.io/badge/CI%20Audit-100%25%20Passing-success?style=for-the-badge&logo=githubactions&logoColor=white)](.github/workflows/ci.yml)
[![Author](https://img.shields.io/badge/Created%20By-Matheus%20Veras-orange?style=for-the-badge)](LICENSE.md)

> **Advanced Acoustic Control Suite, Windows 11 Global DSP Engine, 3D Spatial Audio, and Real-Time Telemetry for Sony & Multi-Brand Headsets.**

Created and engineered by **Matheus Veras**, **Sony Sound Connect PC** addresses the absence of an official Sony companion application for Windows. The project evolved into an industrial-grade acoustic control hub featuring clean Single Responsibility architecture, a 64-bit parametric DSP engine, audiophile AutoEq calibration curves (+5,000 models), and deep integration with native Windows 11 APIs.

---

## ✨ Key Features

### 💎 1. Obsidian Glassmorphism Studio UI (WebView2)
* **Hi-Fi Design:** Modern interface inspired by Logitech G HUB and Windows 11 Mica / Fluent translucency.
* **Interactive B-Spline Frequency Curve:** Real-time canvas-rendered frequency response visualization with interactive control nodes.
* **Native Multi-Language Support (7 Languages):** Complete localization for English (`en-US`), Brazilian Portuguese (`pt-BR`), Japanese (`ja-JP`), Spanish (`es-ES`), German (`de-DE`), Simplified Chinese (`zh-CN`), and French (`fr-FR`) with automatic OS language detection.

### 🔄 2. Multi-Brand Ecosystem & Plugin Architecture
* **Sony MDR V1 Driver:** Serial HPC Protocol (RFCOMM Port 9) with complete support for the **Sony WF-1000XM3** (ANC, Wind Noise Reduction, Ambient Sound, Clear Bass, and touch/sensor controls).
* **Sony Tandem V2 Driver:** Support for **WH-1000XM4**, **WF-1000XM4**, **WH-1000XM5**, and **WF-1000XM5** hardware protocols.
* **Universal Windows 11 Driver:** System-wide EQ and spatial audio enhancement for **Apple AirPods**, **Samsung Galaxy Buds**, **Bose QuietComfort**, **realme Buds**, and any USB/3.5mm headsets.

### 🎛️ 3. Windows 11 Global DSP Engine (Equalizer APO Bridge)
* **64-bit Biquad Parametric Filters:** 6-band acoustic equalizer (Clear Bass + 400Hz, 1kHz, 2.5kHz, 6.3kHz, 16kHz) operating directly inside the Windows kernel audio engine (`AudioDG.exe`).
* **Dynamic Anti-Clipping Preamp:** Real-time headroom computation preventing harmonic distortion and digital clipping.
* **Linkwitz / Chu-Moy 3D Spatial Crossfeed:** Binaural soundstage expansion for gaming, movies, and music, eliminating in-ear acoustic fatigue.

### 🎯 4. Built-In AutoEq Database (+5,000 Headsets)
* Integrated instant search engine covering audiophile target curves (**Harman Target**, Crinacle, Oratory1990, Rtings) applicable with a single click.

### 🪟 5. Native Apple iOS-Style Floating Desktop Overlay
* **Zero Focus Stealing:** High-definition layered card rendered over games and desktop surfaces via Win32 `UpdateLayeredWindow` (`WS_EX_NOACTIVATE`).
* **Automatic Earbud Detection:** Instantly pops up Left (L), Right (R), and Case battery levels whenever earbuds are removed from the case or reconnected.

### ⚡ 6. Zero-Click Auto-Connect & Anti-False Positive Engine
* Windows 11 kernel event listener (`WM_DEVICECHANGE`) for instant zero-click connection upon opening the case.
* **Win32 `BluetoothGetDeviceInfo` Hardware Verification:** Completely eliminates false positives when earbuds are disconnected or stored inside the case.

### 🔋 7. Dynamic System Tray with Semantic Battery LED
* Tray icon displaying real-time connection telemetry and semantic battery status:
  * 🟢 **Green:** Healthy battery (> 35%).
  * 🟡 **Amber:** Moderate battery (20% - 35%).
  * 🔴 **Red:** Critical low battery (< 20%) with smart warning notification.
  * ⚪ **Gray:** Standby / Disconnected.
* Rich context menu for instant EQ preset toggling, ANC modes, and DSP bypass.

### 🩺 8. Hearing Safety Dosimeter & WHO Guidelines Monitor
* Real-time estimated sound pressure level (dB SPL) tracking via Windows CoreAudio COM, providing continuous exposure warnings aligned with World Health Organization (WHO) safety standards.

---

## 🏗️ Software Architecture

Designed with modern **Clean Architecture** and the **Single Responsibility Principle (SRP)**:

```
sony-sound-connect-pc/
├── app/                        # Core Modular Application Package
│   ├── config.py               # Configuration, Paths & Atomic Persistence Manager
│   ├── win32_utils.py          # Low-Level Win32 Subsystems (Mutex, DWM Accent, Taskbar Icon, Language)
│   ├── tray_manager.py         # System Tray Daemon (Semantic LED & Dynamic Telemetry)
│   ├── rpc_bridge.py           # Strongly Typed JS <-> Python RPC Bridge (36 Methods)
│   └── controller.py           # Central Application Orchestrator
├── core/                       # Audio DSP Engine & Hardware Drivers
│   ├── drivers/                # Protocol Drivers (Sony V1, V2 & Universal Windows)
│   ├── windows_apo_engine.py   # Equalizer APO DSP Generator & Biquad Matrix
│   ├── autoeq_database.py      # Indexed AutoEq Database (+5,000 Profiles)
│   ├── ios_desktop_overlay.py  # Non-Activating Native Floating Window (Per-Pixel Alpha)
│   ├── system_integration.py   # Global Hotkeys, App Rules & Kernel Event Watchers
│   └── device_detector.py      # Native Bluetooth Enumerator & Protocol Classifier
├── scripts/                    # Build, Maintenance & Verification Tooling
│   ├── build_standalone_exe.py # Standalone Windows Binary Builder (PyInstaller)
│   ├── package_release.py      # GitHub Release Packager (Portable ZIP & Inno Setup)
│   └── master_audit_and_test_suite.py # 6-Front Automated Quality Gate
├── ui/                         # Modern Frontend Web Assets (HTML5, CSS3, Modular JS)
├── assets/                     # 2K Renders, Official Icons & 3D Visual Assets
├── .github/workflows/ci.yml    # GitHub Actions Continuous Integration (Windows 11)
├── sony_sound_connect_pc.pyw   # Lightweight Clean Entry Point (~75 lines)
├── config.json                 # User Configuration State (Atomic Safe Save)
└── LICENSE.md                  # Proprietary Source-Available License
```

---

## 🚀 Getting Started

### Option 1: Standalone Pre-Built Executable (Recommended)
1. Navigate to the [Releases](https://github.com/MatheusVeras1/sony-sound-connect-pc/releases) page.
2. Download **`SonySoundConnect-v1.0.0-Windows-Portable.zip`** or the installer **`SonySoundConnect-v1.0.0-Setup.exe`**.
3. Double-click the executable to run immediately—no Python installation required.

### Option 2: Running from Source (Developers)
Requires **Python 3.10+** on Windows 11.

```powershell
# 1. Clone the repository
git clone https://github.com/MatheusVeras1/sony-sound-connect-pc.git
cd sony-sound-connect-pc

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the application
python sony_sound_connect_pc.pyw
```

---

## 🔨 Compiling and Packaging Releases

Build a standalone, single-file Windows executable (`.exe`) or distribution packages with a single command:

```powershell
# Build single-file executable (dist/SonySoundConnect.exe)
python scripts/build_standalone_exe.py

# Package portable ZIP and Inno Setup installer script
python scripts/package_release.py
```

---

## 🧪 Automated Quality Gate & Test Suite

The repository includes a comprehensive 6-front automated verification suite:

```powershell
python scripts/master_audit_and_test_suite.py
```

* **Front 1:** Complete Python syntax compilation (.py / .pyw modules).
* **Front 2:** Functional validation of all 36 RPC bridge methods (`window.pywebview.api`).
* **Front 3:** Mathematical verification of 64-bit Biquad filters and AutoEq search performance.
* **Front 4:** Graceful shutdown reliability, deadlock prevention, and Win32 Mutex acquisition.
* **Front 5:** Complete DOM ID audit (106 elements) and full translation verification across 7 languages.
* **Front 6:** Author attribution integrity and licensing compliance.

---

## 👨‍💻 Author & Credits

* **Author & Lead Developer:** [Matheus Veras](https://github.com/MatheusVeras1)
* **License:** Source-Available Proprietary (See [LICENSE.md](LICENSE.md) for full terms).
* **Special Thanks:** The Equalizer APO community and Jaakko Pasanen's AutoEq project.
