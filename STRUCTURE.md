# Project Structure

This document describes the organization of the Medical Inventory System repository.

## Directory Layout

```
Medical-Inventory-System-NASA-Hunch-25-26/
├── src/                          # Source code
│   ├── medical_inventory.py      # Entry point – launches the app
│   ├── app.py                    # Kivy App class (wires screens + KV)
│   ├── constants.py              # Shared constants (columns, admin code, etc.)
│   ├── kv_styles.py              # All Kivy KV layout / style strings
│   ├── widgets.py                # Reusable UI widgets (popups, numpad, rows)
│   ├── screens/                  # One file per application screen
│   │   ├── __init__.py           # Re-exports all screens
│   │   ├── main_screen.py        # Main inventory table + actions
│   │   ├── history_screen.py     # Change-log / history view
│   │   └── personal_screen.py    # Per-user prescriptions & usage
│   ├── database.py               # Database access layer (MySQL)
│   └── facial_recognition.py     # Facial authentication module
│
├── tests/                        # Test suite
│   ├── test_medical_inventory.py # Application tests
│   ├── test_db_manager.py        # Database tests
│   └── run_all_tests.py          # Test runner
│
├── scripts/                      # Installation and startup scripts
│   ├── install_autostart.sh      # Install auto-start configuration
│   ├── uninstall_autostart.sh    # Remove auto-start configuration
│   ├── start_medical_inventory.sh # Application startup script
│   ├── test_autostart_setup.sh   # Validation script
│   └── medical-inventory.service # Systemd service template
│
├── docs/                         # Documentation
│   ├── AUTOSTART_SETUP.md        # Auto-start configuration guide
│   ├── AUTO_START_SUMMARY.md     # Auto-start system overview
│   ├── QUICK_START_AUTOBOOT.md   # Quick start guide
│   ├── RASPBERRY_PI_SETUP.md     # Raspberry Pi deployment guide
│   └── WORKFLOW_TESTING.md       # CI/CD testing documentation
│
├── assets/                       # Static assets
│   ├── references/               # Facial recognition reference images
│   │   ├── brody.png
│   │   ├── lucca.png
│   │   ├── lucca2.png
│   │   └── zach.png
│   ├── transparent_logo.png      # Application logo
│   └── voicerec.html             # Voice recognition prototype
│
├── .github/                      # GitHub configuration
│   └── workflows/                # CI/CD workflows
│       ├── integration-test.yml  # Integration tests
│       ├── raspberry-pi-compat.yml # Pi compatibility tests
│       ├── app-tester.yml        # Application tests
│       └── syntax-check.yml      # Syntax validation
│
├── README.md                     # Main project documentation
├── STRUCTURE.md                  # This file
├── requirements.txt              # Python dependencies
├── inventory.db                  # SQLite database (generated at runtime)
└── .gitignore                    # Git ignore patterns

```

## Key Components

### Source Code (`src/`)
Contains the core application code:
- **medical_inventory.py**: Main Tkinter GUI application for inventory management
- **facial_recognition.py**: Handles user authentication using InsightFace
- **db_manager.py**: SQLite database interface for inventory tracking

### Tests (`tests/`)
Automated test suite:
- Uses pytest framework
- Tests database operations, GUI functionality, and auto-start setup
- Run with `pytest` or `python tests/run_all_tests.py`

### Scripts (`scripts/`)
Installation and deployment scripts:
- Systemd service configuration for auto-start on boot
- Installation and uninstallation scripts
- Startup wrapper for proper environment configuration

### Documentation (`docs/`)
Comprehensive guides:
- Auto-start configuration and troubleshooting
- Raspberry Pi 4 deployment instructions
- CI/CD testing documentation

### Assets (`assets/`)
Static files:
- Reference images for facial recognition
- Application logos and resources

## Usage

### Running the Application
```bash
# From repository root
python3 src/medical_inventory.py
```

### Running Tests
```bash
# From repository root
pytest tests/
```

### Installing Auto-Start
```bash
# From repository root
sudo ./scripts/install_autostart.sh
```

## Development

When adding new features:
1. Source code goes in `src/`
2. Tests go in `tests/`
3. Documentation goes in `docs/`
4. Scripts go in `scripts/`

This structure keeps the repository organized and maintainable.
