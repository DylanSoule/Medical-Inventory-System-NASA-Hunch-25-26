# Medical Inventory System — NASA HUNCH 2025‑26

A facial‑authenticated medical inventory management system built for the NASA HUNCH 2025‑2026 program.  
Runs on a Raspberry Pi 4 for low-power, embedded deployment suitable for constrained or remote environments (e.g. space habitation modules).

> **Note:** This project is still under active development.

---

## Table of Contents

- [About](#about)
- [Implemented Features](#implemented-features)
- [Planned / Roadmap](#planned--roadmap)
- [Architecture & Components](#architecture--components)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
  - [One-Step Installer](#one-step-installer)
  - [Manual Setup](#manual-setup)
  - [Database Setup](#database-setup)
  - [Facial Reference Preparation](#facial-reference-preparation)
  - [Usage](#usage)
  - [Auto-Start (systemd)](#auto-start-systemd)
- [Facial Recognition Module](#facial-recognition-module)
- [Troubleshooting](#troubleshooting)
- [Project Status](#project-status)
- [Structure Reference](#structure-reference)
- [License](#license)
- [Contact](#contact)
- [Future Contributions](#future-contributions)

---

## About

The Medical Inventory System is designed to help medical facilities — specifically those on space stations or aboard space missions — track medication supplies, manage stock levels, monitor usage history, and control access securely using facial recognition.

Developed for the NASA HUNCH 2025‑26 program, the system runs efficiently on a Raspberry Pi 4 or similar embedded device. It features a fullscreen Kivy GUI with three dedicated screens: a main inventory view, a change-history log with anomaly detection, and a per-user prescription & usage tracker. The system can be configured to start automatically on boot, creating a dedicated kiosk-style medical inventory station.

---

## Implemented Features

- **Facial recognition** (InsightFace + ONNX Runtime) gates all inventory actions; model and camera are pre-loaded in the background for fast response.
- **MySQL-backed storage** for all inventory data, change history, people, and prescriptions.
- **Three-screen Kivy GUI** (fullscreen):
  - **Main Screen** — inventory table with column toggles, type filtering, search, and background auto-refresh.
  - **History Screen** — change-log of drug additions/removals over the last 7 days; includes pattern-recognition anomaly detection.
  - **Personal Screen** — per-user view of scheduled prescriptions, daily usage history, and as-needed medications.
- **Admin-gated actions** protected by a PIN code (`ADMIN_CODE` in `constants.py`).
- **Systemd auto-start** installation and uninstallation scripts for kiosk-style deployment on Raspberry Pi.
- **One-step installer** (`MIS_installer.sh`) that installs all system dependencies, sets up a Dockerised MySQL database, configures a Python virtual environment, and installs the systemd service.
- **Error reporting** via a typed `FaceRecognitionError` enum with distinct codes for each failure mode.

---

## Planned / Roadmap

| Category | Planned Enhancements |
|----------|----------------------|
| Access Control | Replace hard-coded admin PIN with a secure credential store; configurable roles (Admin / User) |
| Data Operations | CSV / JSON export button; inline editing of inventory entries |
| Alerts | Low-quantity and expiration-date warnings |
| Interface | Touch-friendly input improvements; responsive column scaling |
| Remote Ops | Optional cloud sync / remote dashboard |
| Configuration | External config file or env vars for thresholds, admin code, and DB connection |
| Reliability | Automatic database backup / integrity checks |
| Debug | Optional verbose debug flag for facial recognition and DB layers |

---

## Architecture & Components

| Component / Path | Purpose |
|------------------|---------|
| `src/medical_inventory.py` | Entry point — launches `MedicalInventoryApp` |
| `src/app.py` | Kivy `App` subclass — loads KV styles, creates `ScreenManager` with all three screens |
| `src/constants.py` | Shared constants (`COLUMNS`, `ADMIN_CODE`, `REFRESH_INTERVAL`) |
| `src/kv_styles.py` | All Kivy KV layout and style strings |
| `src/widgets.py` | Reusable UI widgets: `NumpadWidget`, popups, `DataRow`, `HeaderRow` |
| `src/screens/main_screen.py` | Main inventory table with search, filtering, and admin actions |
| `src/screens/history_screen.py` | Change-log view and pattern-recognition anomaly results |
| `src/screens/personal_screen.py` | Per-user prescriptions, daily usage history, and as-needed medications |
| `src/database.py` | `DatabaseManager` (inventory-wide) and `PersonalDatabaseManager` (per-user); all MySQL access |
| `src/facial_recognition.py` | InsightFace model loading, camera management, and threaded face detection |
| `database_setup/mysql_database_construction.txt` | MySQL `CREATE TABLE` statements |
| `database_setup/seeder.py` | Seeds the database with test data from CSV files |
| `assets/references/` | Authorized user facial reference images (filenames map to user IDs) |
| `MIS_installer.sh` | One-step installer: system deps, Docker DB, Python venv, systemd service |
| `scripts/install_autostart.sh` | Creates systemd service for kiosk auto-launch |
| `scripts/uninstall_autostart.sh` | Removes the systemd service |
| `scripts/start_medical_inventory.sh` | Launch wrapper used by the systemd service |
| `docs/` | Supplemental deployment & setup documentation |
| `STRUCTURE.md` | Extended repository layout explanation |
| Hardware | Raspberry Pi 4, USB webcam, HID USB barcode scanner, HDMI display |

---

## Prerequisites

### Hardware (Raspberry Pi 4 Target)

- Raspberry Pi 4 (2 GB min; 4 GB+ recommended)
- MicroSD (16 GB+ Class 10 / UHS-I)
- USB Webcam or Pi Camera Module
- USB Barcode Scanner (HID keyboard emulation)
- HDMI Display / Touchscreen
- Adequate cooling (optional but recommended)

### Software

- Raspberry Pi OS 64-bit with Desktop (Bookworm / Bullseye)
- Python 3.10+
- Docker & Docker Compose (for the MySQL database container — installed automatically by `MIS_installer.sh`)
- Pip packages (see `requirements.txt`):
  - `kivy>=2.3.0`
  - `mysql-connector-python>=8.0.0`
  - `opencv-python>=4.8.0`
  - `numpy>=1.24.0`
  - `insightface>=0.7.3`
  - `onnxruntime>=1.16.0`
  - `scikit-learn>=1.3.0`
  - `scikit-image>=0.21.0`
  - `pytest>=7.4.0` (for tests)

---

## Installation & Setup

### One-Step Installer

The easiest way to get started on a Raspberry Pi (or any Debian-based system):

```bash
git clone https://github.com/DylanSoule/Medical-Inventory-System-NASA-Hunch-25-26.git
cd Medical-Inventory-System-NASA-Hunch-25-26
sudo bash MIS_installer.sh
```

The installer will:
1. Install system packages (`git`, `python3`, `python3-pip`, `python3-venv`, `docker.io`, `docker-compose`).
2. Start Docker and add your user to the `docker` group.
3. Create a Python virtual environment and install all `requirements.txt` dependencies.
4. Start a MySQL database Docker container (`medical-inventory-db`).
5. Make scripts executable and install the systemd auto-start service.

After installation you will be prompted to start the service immediately or wait until the next reboot.

### Manual Setup

1. Clone repository:
   ```bash
   git clone https://github.com/DylanSoule/Medical-Inventory-System-NASA-Hunch-25-26.git
   cd Medical-Inventory-System-NASA-Hunch-25-26
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install Python dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Ensure your USB webcam and barcode scanner are connected.

### Database Setup

The application requires a running MySQL server with the `inventory_system` database.

**Using Docker (recommended):**
```bash
docker run -d \
  --name medical-inventory-db \
  -e MYSQL_ROOT_PASSWORD=1234 \
  -e MYSQL_DATABASE=inventory_system \
  -p 3306:3306 \
  --restart unless-stopped \
  mysql:8
```

**Create tables:**
```bash
mysql -u root -p1234 inventory_system < database_setup/mysql_database_construction.txt
```

**Seed with test data (optional):**
```bash
python3 database_setup/seeder.py
```

> The default DB credentials (`root` / `1234`) are defined in `src/database.py`. Change them to match your environment before deploying.

### Facial Reference Preparation

Place one or more clear, frontal-face images per authorized user in:
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
- Filenames become user IDs with trailing digits stripped and the first character capitalized (e.g. `alice.jpg` → `Alice`).

### Usage

Run the application:
```bash
python3 src/medical_inventory.py
```

**Main Screen**
1. The facial recognition model and camera pre-load in the background on startup.
2. Select a drug type filter or use the search bar to narrow results.
3. Toggle visible columns using the checkboxes in the header bar.
4. Admin-gated actions (add, remove, delete) require facial recognition and the admin PIN.

**History Screen**
- Navigate to the History screen to view the last 7 days of drug-change events.
- Tap "Pattern Recognition" to run the anomaly-detection algorithm.

**Personal Screen**
- After facial recognition, the Personal screen shows the identified user's scheduled prescriptions, today's usage history, and as-needed medications.
- Use the day-navigation arrows to review previous days.

### Auto-Start (systemd)

Install the unit for kiosk auto-launch:
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

For full Raspberry Pi deployment instructions (auto-login, screen blanking, performance tuning), see [docs/RASPBERRY_PI_SETUP.md](docs/RASPBERRY_PI_SETUP.md).

---

## Facial Recognition Module

**Process (simplified):**
1. `preload_everything()` loads the InsightFace `buffalo_sc` model and computes normalized embeddings for all reference images; the camera is also opened and kept warm.
2. `quick_detect()` is called when an action requires authentication — it runs threaded frame capture and embedding matching against the pre-loaded references.
3. A face is confirmed when the nearest-neighbor distance falls below `THRESHOLD = 1`.
4. Detection times out after 15 seconds if no known face is found.

**Return values from `quick_detect()` / `main()`:**

| Return value | Meaning |
|---|---|
| `list[str]` (non-empty) | Recognized user label(s) |
| `[]` (empty list) | System not ready or no known face detected within timeout |
| `FaceRecognitionError.MODEL_LOAD_FAILED` (1) | InsightFace model could not be loaded |
| `FaceRecognitionError.REFERENCE_FOLDER_ERROR` (2) | `assets/references/` folder missing or inaccessible |
| `FaceRecognitionError.PRELOAD_FAILED` (3) | General pre-load initialization failure |
| `FaceRecognitionError.CAMERA_ERROR` (4) | Camera could not be opened |
| `FaceRecognitionError.CAMERA_DISCONNECTED` (5) | Camera disconnected during operation |
| `FaceRecognitionError.FRAME_CAPTURE_FAILED` (6) | Failed to capture a frame |
| `FaceRecognitionError.UNKNOWN_ERROR` (99) | Unexpected error |

---

## Troubleshooting

| Symptom | Possible Cause | Action |
|---------|----------------|--------|
| `CAMERA_ERROR` (4) | Webcam not detected or busy | Check `/dev/video*`, reconnect device, ensure user is in `video` group |
| `CAMERA_DISCONNECTED` (5) | Camera unplugged during session | Reconnect camera; the app will attempt re-initialization |
| `REFERENCE_FOLDER_ERROR` (2) | Missing `assets/references/` | Create the folder and add at least one frontal-face image |
| No face recognized (returns `[]`) | Poor lighting, face occluded, or threshold too strict | Use clear, well-lit images; adjust `THRESHOLD` in `facial_recognition.py` |
| DB connection refused | MySQL container not running | Run `docker start medical-inventory-db` or restart the Docker service |
| Blank inventory table | No data in DB or wrong credentials | Run the seeder; verify credentials in `src/database.py` |
| Admin action denied | Wrong admin PIN | Currently hard-coded as `"1234"` in `src/constants.py` (`ADMIN_CODE`) |
| Slow first launch | Model loading on first run | Subsequent runs are faster; camera and model are pre-loaded on startup |
| High CPU / memory on Pi | Full-resolution frame processing | Increase `frame_count % N` throttle in `facial_recognition.py` |

---

## Project Status

Active development. Current focus areas:
- Stabilizing facial recognition authentication flow on Raspberry Pi hardware.
- Replacing the hard-coded admin PIN with a secure credential store.
- Adding CSV/JSON export and inline inventory editing.
- Improving low-quantity and expiration-date alert system.

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
- Coding standards (PEP 8 + type hints).
- Facial image enrollment procedure.
- Security hardening steps (PIN storage, least privilege, DB credential management).

### Development Workflow

We use an automated workflow to streamline development:

**Auto-Assign Issues Workflow**: When you create a branch with an issue number in its name (e.g., `issue-123`, `42-feature-name`), our GitHub Actions workflow automatically:
- Creates a draft pull request
- Links the issue to the PR
- Moves the issue to "In Progress" in project boards
- Auto-generates PR title and description

See [Auto-Assign Workflow Documentation](docs/AUTO_ASSIGN_WORKFLOW.md) for detailed usage instructions.

For now, feel free to open issues or pull requests with clear descriptions.

---
