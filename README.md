# PowerSupply Controller

Desktop application (Windows) for controlling programmable power supplies over Serial/USB.

This repository currently targets:
- `GW Instek GPP-3323`
- `Keysight / Agilent E3646A`

The app provides a Tkinter GUI for connection, voltage/current control, protection setup, run modes, configuration persistence, and in-app update checks.

## Architecture

- `sources/main.py`: process entrypoint only.
- `sources/ui/main_view.py`: UI composition and event wiring.
- `sources/controllers/app_controller.py`: stateful controller for business flow and side effects.
- `sources/app_core/*`: reusable low-level services (serial, config, update, paths, logging, pure range helpers).

## Product Features

### 1) Device and COM management
- Scan available COM ports
- Connect/disconnect with selected baud rate
- Device identity validation using `*IDN?`
- Device profile switch (`GPP-3323` or `Keysight`)

### 2) Output and electrical controls
- Set voltage and current
- Output ON/OFF control
- OVP (Over Voltage Protection) ON/OFF + value
- OCP (Over Current Protection) ON/OFF + value
- Optional response readback from instrument (`Read Resp: ON/OFF`)

### 3) Voltage execution modes
- Mode 1: preset voltage list (multiple boxes)
- Mode 2: manual single value input
- Mode 3: range mode (start/end/step/delay, resume and reverse support)
- Auto-run with configurable delay
- Step increase/decrease and next-voltage navigation

### 4) Configuration and persistence
- Save setup to JSON file
- Load JSON config back to UI
- Persist includes device, COM, baud rate, voltages, mode, protections, reverse order

### 5) Update and installer flow
- Check latest release from GitHub Releases API
- Compare semantic-like versions
- Download update package with progress dialog
- Optional uninstall-then-install workflow
- Launch installer (`.exe`/`.msi`) after download

### 6) Companion voice app
- `voice_app.py` supports Vietnamese voice-to-number input into active Excel cell
- Packaged as a secondary executable in installer

## Repository Structure

```text
.
|- assets/                       # icons/images
|- sources/
|  |- main.py                    # thin entrypoint
|  |- controllers/
|  |  `- app_controller.py       # application state + business logic
|  |- ui/
|  |  `- main_view.py            # Tkinter widget tree and bindings
|  |- voice_app.py               # optional voice companion app
|  |- MyGPPInstaller.iss         # Inno Setup script
|  `- app_core/                  # refactored reusable core services
|     |- config_store.py         # JSON config IO
|     |- logging_utils.py        # rotating file logger setup
|     |- paths.py                # AppData path/bootstrap + resource resolution
|     |- range_utils.py          # pure helpers for stepping/range logic
|     |- serial_service.py       # COM/Serial connection and IDN validation
|     |- update_service.py       # release metadata fetch and asset selection
|     `- versioning.py           # version parsing/comparison + version file read
|- build.bat                     # build helper for PyInstaller
|- main.spec                     # PyInstaller spec for main app
|- voice_app.spec                # PyInstaller spec for voice app
|- requirements.txt
|- requirements-dev.txt
|- pyproject.toml                # Ruff configuration
|- tests/
|  `- test_range_utils.py
`- scripts/
   `- setup_env.ps1              # .venv bootstrap script
```

## Tech Stack

- Python 3.10+ (tested with 3.13)
- Tkinter (desktop UI)
- `pyserial` (serial communication)
- `requests` (GitHub update API + download)
- `Pillow` (icon/image processing for Tkinter UI)
- `SpeechRecognition`, `PyAudio`, `pywin32` (voice companion app)
- PyInstaller (packaging executable)
- Inno Setup (Windows installer)

## Quick Start (Production-like local setup)

### Option A: one command bootstrap (recommended)

```powershell
.\scripts\setup_env.ps1
```

For development dependencies too:

```powershell
.\scripts\setup_env.ps1 -Dev
```

### Option B: manual setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run

```powershell
.\.venv\Scripts\python.exe sources\main.py
```

Voice companion:

```powershell
.\.venv\Scripts\python.exe sources\voice_app.py
```

## Build Executables

### Using existing batch script

```powershell
build.bat
```

### Or direct PyInstaller commands

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --onedir --windowed --icon=assets\myicon.ico sources\main.py
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --onedir --windowed sources\voice_app.py
```

## Build Installer

1. Ensure `dist/main` and `dist/voice_app` exist.
2. Build installer from `sources/MyGPPInstaller.iss` with Inno Setup.
3. Output is generated into `Output/` (e.g., `PowerSupplyController.exe`).

## Runtime Data Paths

At runtime, app data is created under:

`%APPDATA%\PowerSupply Controller\`

- `config\` for saved JSON configurations
- `download\` for downloaded update installers
- `temp\` for temporary files
- `app.log` for runtime logs (rotating file)

## Validation Commands

```powershell
.\.venv\Scripts\python.exe -m py_compile sources\main.py sources\voice_app.py
.\.venv\Scripts\python.exe -m compileall sources
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
```

## Notes

- This project is Windows-first because COM control, installer flow, and voice dependencies are Windows-oriented.
- Keep `.venv/`, `build/`, `dist/` out of version control (already configured in `.gitignore`).
