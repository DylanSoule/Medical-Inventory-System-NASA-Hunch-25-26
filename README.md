# Medical Inventory System — NASA HUNCH 2025‑26

![Raspberry Pi Compat](https://github.com/DylanSoule/Medical-Inventory-System-NASA-Hunch-25-26/actions/workflows/raspberry-pi-compat.yml/badge.svg)
![Python Tests](https://github.com/DylanSoule/Medical-Inventory-System-NASA-Hunch-25-26/actions/workflows/app-tester.yml/badge.svg)
![Syntax Check](https://github.com/DylanSoule/Medical-Inventory-System-NASA-Hunch-25-26/actions/workflows/syntax-check.yml/badge.svg)

A facial‑authenticated medical inventory scan logging system built for the NASA HUNCH 2025‑2026 program.  
Runs on a Raspberry Pi 4 for low power, embedded deployment suitable for constrained or remote environments (e.g. space habitation modules).

Note: This project is still under development


---

## Table of Contents

- [About](#about)
- [Implemented Features](#implemented-features)
- [Planned / Roadmap](#planned--roadmap)
- [Architecture & Components](#architecture--components)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
  - [Facial Reference Preparation](#facial-reference-preparation)
  - [Usage](#usage)
  - [Auto-Start (systemd)](#auto-start-systemd)
  - [Raspberry Pi Quick Deploy](#raspberry-pi-quick-deploy)
- [Facial Recognition Module](#facial-recognition-module)
- [Troubleshooting](#troubleshooting)
- [Project Status](#project-status)
- [Structure Reference](#structure-reference)
- [License](#license)
- [Contact](#contact)
- [Future Contributions](#future-contributions)

---

## About

The Medical Inventory System is designed to help medical facilities, specifically ones on space stations or aboard space missions, track supplies, manage stock levels, and control access securely using facial recognition.
Developed for the NASA Hunch 2025-26 program, the system runs efficiently on a Raspberry Pi 4 or similar embedded device — suitable for low-power, remote, or space environments. The system can be configured to start automatically on boot, creating a dedicated kiosk-style medical inventory station.

---

## Implemented Features

- Facial recognition (InsightFace + ONNX Runtime) prior to logging a scan.
- SQLite-backed storage of scan events (`scans` table).
- Deletion with:
  - Mandatory reason
  - Admin PIN 
  - Persistent audit trail (`deletion_history` table)
- Fullscreen Tkinter GUI
- Deletion history viewer (separate window).
- Systemd auto-start installation script for kiosk-style deployment on Raspberry Pi.
- Error reporting & return codes from facial recognition module.

---

## Planned / Roadmap

| Category | Planned Enhancements |
|----------|----------------------|
| Inventory Logic | Distinct Add / Remove actions; quantity aggregation per item |
| Data Operations | Edit existing entries, search/filter UI, CSV/JSON export button |
| Access Control | Configurable roles (Admin / User); secure PIN or credential store |
| Alerts | Low quantity / expiration warnings |
| Interface | Real-time refresh (event-driven), responsive scaling |
| Remote Ops | Optional cloud sync / dashboard |
| Configuration | External config file or env vars for thresholds, admin code, paths |
| Reliability | Automatic database backup / integrity checks |

---

## Architecture & Components

| Component / Path | Purpose |
|------------------|---------|
| `src/medical_inventory.py` | Main Tkinter GUI; scan logging, deletion, history view |
| `src/facial_recognition.py` | Face detection & identification (returns recognized names list or error code) |
| `src/db_manager.py` | SQLite access layer (tables: `scans`, `deletion_history`) |
| `inventory.db` | Primary SQLite database (created automatically if missing) |
| `assets/references/` | Authorized user facial reference images (filenames map to user IDs) |
| `scripts/install_autostart.sh` | Creates systemd service for kiosk auto-launch |
| `scripts/uninstall_autostart.sh` | Removes the systemd service |
| `scripts/start_medical_inventory.sh` | Launch wrapper for GUI app |
| `tests/` | Test suite scaffolding (database & functional tests) |
| `docs/` | Supplemental deployment & setup documentation |
| `STRUCTURE.md` | Extended repository layout explanation |
| Hardware | Raspberry Pi 4, USB camera/webcam, HID USB barcode scanner, display |

---




## Prerequisites

### Hardware (Raspberry Pi 4 Target)

- Raspberry Pi 4 (2GB min; 4GB+ recommended)
- MicroSD (16GB+ Class 10 / UHS-I)
- USB Webcam or Pi Camera Module
- USB Barcode Scanner (HID keyboard emulation)
- HDMI Display / Touchscreen
- Adequate cooling (optional but recommended)

### Software

- Raspberry Pi OS (64-bit with Desktop recommended)
- Python 3.10+
- System packages: `python3-tk`, `python3-opencv` (or install via apt)
- Pip packages (see requirements.txt):
  - opencv-python
  - numpy
  - insightface
  - onnxruntime
  - scikit-learn
  - scikit-image
  - pytest (for tests)

> Tkinter is a system package; do NOT `pip install tk`. Use OS package manager.

---

## Installation & Setup

1. Clone repository:
   ```bash
   git clone https://github.com/DylanSoule/Medical-Inventory-System-NASA-Hunch-25-26.git
   cd Medical-Inventory-System-NASA-Hunch-25-26
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure camera & barcode scanner are connected.

### Facial Reference Preparation

Place one or more clear, frontal images per authorized user in:
```
assets/references/
```
Example filenames:
```
alice.jpg
bob.jpeg
charlie_1.png
```
Naming rules:
- One face per image.
- Filenames become user IDs with trailing digits removed & sanitized.

### Usage

Run GUI:
```bash
python3 src/medical_inventory.py
```

Process:
1. Click “Log Scan”.
2. Complete facial recognition window; on success you are prompted for barcode.
3. Scan (or type) barcode; press Enter or OK.
4. Entry appears in the table.

View deletion history:
- Click “View Deletion History” (admin PIN required).

Delete selected rows:
1. Select rows in table.
2. Click “Delete Selected” (admin PIN required).
3. Provide mandatory reason.

### Auto-Start (systemd)

Install unit for kiosk auto-launch:
```bash
sudo ./scripts/install_autostart.sh
```

Useful systemd commands:
```bash
sudo systemctl start medical-inventory@$USER.service
sudo systemctl status medical-inventory@$USER.service
sudo journalctl -u medical-inventory@$USER.service -f
sudo systemctl disable medical-inventory@$USER.service
```

Uninstall:
```bash
sudo ./scripts/uninstall_autostart.sh
```

### Raspberry Pi Quick Deploy

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3-pip python3-tk python3-opencv
git clone https://github.com/DylanSoule/Medical-Inventory-System-NASA-Hunch-25-26.git
cd Medical-Inventory-System-NASA-Hunch-25-26
pip install -r requirements.txt
sudo ./scripts/install_autostart.sh
sudo raspi-config   # (optional) enable auto-login
sudo reboot
```

---

## Facial Recognition Module

Process (simplified):
1. Load InsightFace model.
2. Read reference images, compute normalized embeddings.
3. Capture live frames, detect faces, compute embeddings.
4. Match embedding to nearest reference under threshold.
5. Return list of recognized names (or error code).



Return values:
- `[]` (empty list) — no valid reference faces loaded.
- `list[str]` — recognized user labels.
- `2` — could not read a reference image.
- `3` — reference folder missing OR no face detected in reference image.
- `4` — camera could not be opened.

---



## Troubleshooting

| Symptom | Possible Cause | Action |
|---------|----------------|--------|
| “Camera Error” (code 4) | Webcam not detected / busy | Check `/dev/video0`, reconnect device |
| “Reference Folder Error” (code 3) | Missing `assets/references/` or no detectable face | Create folder; ensure frontal face |
| “No Faces Found” (code 3) | Poor image quality / face occluded | Replace images with clear, single faces |
| Blank GUI table | No scans yet / DB corruption | Check `inventory.db` permissions |
| Deletion denied | Wrong admin PIN | Currently hard-coded: `1234` |
| High recognition delay | Model load first run | Subsequent sessions faster; consider caching |
| False “Unknown” | Threshold too strict | Future config: adjust THRESHOLD |

Log verbose debugging (future): implement optional debug flag.

---

## Project Status

Active development. Current focus areas:
- Stabilizing facial recognition workflow.
- Implementing inventory quantity logic.
- Adding search/filter & export UI.
- Replacing hard-coded admin PIN.

---

## Structure Reference

See [STRUCTURE.md](STRUCTURE.md) for an expanded explanation of directory layout and intended future modules.

---

## License

Licensed under the MIT License. See [LICENSE](LICENSE) for full text.

---

## Contact

**NASA HUNCH 2025‑26 Medical Inventory Team**  
Maintainers: Dylan Soule, Brody Barnes, Lucca Townsend, Zach Stelman  
Email: dylan.soule@icloud.com    
Brainstorming Board: [Miro Workspace](https://miro.com/app/board/uXjVJIvb3LU=/)

---

## Future Contributions

Planned contribution guidelines will include:
- Issue templates for feature / bug / enhancement.
- Coding standards (PEP8 + type hints).
- Facial image enrollment procedure.
- Security hardening steps (PIN storage, least privilege).

For now, feel free to open issues or pull requests with clear descriptions.

---

