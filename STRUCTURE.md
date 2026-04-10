# Project Structure

This document describes the organization of the Medical Inventory System repository.

## Directory Layout

```
Medical-Inventory-System-NASA-Hunch-25-26/
├── src/                              # Source code
│   ├── medical_inventory.py          # Entry point – launches the app
│   ├── app.py                        # Kivy App class (wires screens + KV)
│   ├── constants.py                  # Shared constants (columns, admin code, refresh interval)
│   ├── kv_styles.py                  # All Kivy KV layout / style strings
│   ├── widgets.py                    # Reusable UI widgets (popups, numpad, table rows)
│   ├── screens/                      # One file per application screen
│   │   ├── __init__.py               # Re-exports all screens
│   │   ├── main_screen.py            # Main inventory table + actions
│   │   ├── history_screen.py         # Change-log / history view
│   │   └── personal_screen.py        # Per-user prescriptions & usage
│   ├── database.py                   # Database access layer (MySQL)
│   └── facial_recognition.py         # Facial authentication module (InsightFace)
│
├── database_setup/                   # Database initialisation
│   ├── mysql_database_construction.txt  # CREATE TABLE statements
│   ├── seeder.py                     # Seed script for test data
│   └── seeder_csvs/                  # CSV files used by seeder
│       ├── assigned_prescriptions.csv
│       ├── history.csv
│       ├── in_inventory.csv
│       ├── medications.csv
│       ├── people.csv
│       └── prescriptions.csv
│
├── scripts/                          # Installation and startup scripts
│   ├── install_autostart.sh          # Install auto-start configuration
│   ├── uninstall_autostart.sh        # Remove auto-start configuration
│   ├── start_medical_inventory.sh    # Application startup script
│   ├── test_autostart_setup.sh       # Validation script
│   └── medical-inventory.service     # Systemd service template
│
├── docs/                             # Documentation
│   ├── AUTOSTART_SETUP.md            # Auto-start configuration guide
│   ├── AUTO_START_SUMMARY.md         # Auto-start system overview
│   ├── QUICK_START_AUTOBOOT.md       # Quick start guide
│   ├── RASPBERRY_PI_SETUP.md         # Raspberry Pi deployment guide
│   └── WORKFLOW_TESTING.md           # CI/CD testing documentation
│
├── assets/                           # Static assets
│   └── references/                   # Facial recognition reference images
│
├── .github/                          # GitHub configuration
│   └── workflows/                    # CI/CD workflows
│       └── auto-assign-issues.yml    # Auto-assign issues
│
├── README.md                         # Main project documentation
├── STRUCTURE.md                      # This file
├── requirements.txt                  # Python dependencies
├── MIS_installer.sh                  # One-step installer script
└── .gitignore                        # Git ignore patterns
```

## Key Components

### Source Code (`src/`)

The application follows a modular Kivy architecture:

| File | Purpose |
|------|---------|
| `medical_inventory.py` | Thin entry point — runs `MedicalInventoryApp` |
| `app.py` | Kivy `App` subclass — loads KV, creates `ScreenManager` |
| `constants.py` | Shared constants (`COLUMNS`, `ADMIN_CODE`, `REFRESH_INTERVAL`) |
| `kv_styles.py` | All KV language layout / style definitions |
| `widgets.py` | Reusable widgets: `NumpadWidget`, popups, `DataRow`, `HeaderRow` |
| `screens/` | One `Screen` subclass per file (`main`, `history`, `personal`) |
| `database.py` | `DatabaseManager` + `PersonalDatabaseManager` (MySQL) |
| `facial_recognition.py` | InsightFace model loading, camera management, face detection |

### Database Setup (`database_setup/`)
- MySQL schema definitions and a CSV-based seeder for test data.
- Tables: `medications`, `in_inventory`, `people`, `prescriptions`, `assigned_prescriptions`, `history`.

### Scripts (`scripts/`)
- Systemd service configuration for Raspberry Pi auto-start on boot.
- Installation, uninstallation, and startup wrapper scripts.

### Documentation (`docs/`)
- Auto-start configuration and troubleshooting guides.
- Raspberry Pi 4 deployment instructions.

## Usage

### Running the Application
```bash
# From repository root
python3 src/medical_inventory.py
```

### Setting Up the Database
```bash
# Create tables using mysql_database_construction.txt, then seed:
python3 database_setup/seeder.py
```

### Installing Auto-Start (Raspberry Pi)
```bash
sudo ./scripts/install_autostart.sh
```

## Development

When adding new features:
1. Source code goes in `src/`
2. New screens go in `src/screens/` (add to `__init__.py`)
3. Shared widgets go in `src/widgets.py`
4. Documentation goes in `docs/`
5. Scripts go in `scripts/`

This structure keeps the repository organized and maintainable.
