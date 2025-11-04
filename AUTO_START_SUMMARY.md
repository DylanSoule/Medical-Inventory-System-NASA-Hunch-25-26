# Auto-Start System Summary

## Overview

The Medical Inventory System has been configured to run automatically on startup, transforming a **Raspberry Pi 4** into a dedicated medical inventory kiosk system.

## What Was Added

### Core Auto-Start Files

1. **`install_autostart.sh`** - Installation script
   - Creates systemd service
   - Enables auto-start on boot
   - Sets proper permissions
   - Run with: `sudo ./install_autostart.sh`

2. **`uninstall_autostart.sh`** - Uninstallation script
   - Removes auto-start configuration
   - Stops running service
   - Run with: `sudo ./uninstall_autostart.sh`

3. **`start_medical_inventory.sh`** - Startup script
   - Waits for X server to be ready
   - Activates Python virtual environment (if exists)
   - Launches the application
   - Logs startup events

4. **`medical-inventory.service`** - Systemd service template
   - Defines service behavior
   - Sets environment variables
   - Configures auto-restart on failure

### Documentation Files

1. **`RASPBERRY_PI_SETUP.md`** (11KB)
   - Complete Raspberry Pi 4 setup guide
   - Hardware requirements
   - Step-by-step installation
   - Performance optimization
   - Troubleshooting guide
   - Security recommendations

2. **`AUTOSTART_SETUP.md`** (6.5KB)
   - Detailed auto-start configuration
   - Systemd service management
   - Kiosk mode setup
   - Advanced configuration options

3. **`QUICK_START_AUTOBOOT.md`** (2KB)
   - Quick reference guide
   - Essential commands
   - Common troubleshooting

4. **`README.md`** (Updated)
   - Added auto-start section
   - Added Raspberry Pi 4 deployment guide
   - Updated prerequisites
   - Added hardware specifications

### Testing & Validation

1. **`test_autostart_setup.sh`** - Validation script
   - Tests all setup files
   - Validates script syntax
   - Checks documentation
   - Run with: `./test_autostart_setup.sh`

2. **`.gitignore`** - Git ignore rules
   - Excludes logs
   - Excludes virtual environments
   - Excludes build artifacts

## How It Works

### Boot Sequence

1. **Raspberry Pi 4 boots** → Raspberry Pi OS starts
2. **Graphical environment loads** → LXDE desktop starts
3. **Systemd activates service** → `medical-inventory@user.service` starts
4. **Startup script runs** → Waits for X server, sets environment
5. **Application launches** → Medical Inventory System opens in fullscreen
6. **User ready** → System ready for facial recognition and barcode scanning

### Architecture

```
Raspberry Pi 4 Boot
       ↓
Raspberry Pi OS (Debian-based)
       ↓
systemd (medical-inventory@user.service)
       ↓
start_medical_inventory.sh
       ↓
Python 3 + Virtual Environment
       ↓
medical_inventory.py (Main Application)
       ↓
Fullscreen GUI Ready
```

## Installation Quick Steps

### For Raspberry Pi 4:

1. **Flash SD card** with Raspberry Pi OS (64-bit with Desktop)
2. **Boot and update**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
3. **Clone repository**:
   ```bash
   git clone https://github.com/DylanSoule/Medical-Inventory-System-NASA-Hunch-25-26.git
   cd Medical-Inventory-System-NASA-Hunch-25-26
   ```
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
5. **Install auto-start**:
   ```bash
   sudo ./install_autostart.sh
   ```
6. **Enable auto-login**:
   ```bash
   sudo raspi-config
   # System Options → Boot / Auto Login → Desktop Autologin
   ```
7. **Reboot**:
   ```bash
   sudo reboot
   ```

## Key Features

### Automatic Startup
- Launches automatically when Raspberry Pi 4 boots
- No manual intervention required
- Ideal for dedicated kiosk deployments

### Reliability
- Auto-restart on failure (5 second delay)
- Systemd service management
- Proper error handling and logging

### Raspberry Pi 4 Optimization
- Configured for 64-bit Raspberry Pi OS
- GPU memory allocation recommendations
- Performance tuning guidance
- Hardware-specific troubleshooting

### Kiosk Mode
- Fullscreen by default
- Screen blanking prevention
- Mouse cursor hiding (optional)
- Auto-login support

### Easy Management
```bash
# Start service
sudo systemctl start medical-inventory@$USER.service

# Stop service
sudo systemctl stop medical-inventory@$USER.service

# Check status
sudo systemctl status medical-inventory@$USER.service

# View logs
sudo journalctl -u medical-inventory@$USER.service -f

# Disable auto-start
sudo systemctl disable medical-inventory@$USER.service

# Uninstall completely
sudo ./uninstall_autostart.sh
```

## Hardware Requirements (Raspberry Pi 4)

- **Computer**: Raspberry Pi 4 Model B
  - RAM: 2GB minimum (4GB or 8GB recommended)
- **Storage**: MicroSD card, 16GB minimum (32GB+ recommended, Class 10)
- **Power**: Official Raspberry Pi 5V 3A USB-C power supply
- **Camera**: USB Webcam or Raspberry Pi Camera Module v2/v3
- **Input**: USB Barcode Scanner (HID keyboard mode)
- **Display**: HDMI monitor or touchscreen
- **Optional**: Heatsinks or cooling fan

## Software Stack

- **OS**: Raspberry Pi OS 64-bit with Desktop (Debian Bullseye or newer)
- **Python**: 3.10+ (included with Raspberry Pi OS)
- **GUI**: Tkinter (python3-tk)
- **Computer Vision**: OpenCV (opencv-python)
- **Facial Recognition**: InsightFace + ONNX Runtime
- **Database**: SQLite (db_manager.py)
- **Service Manager**: systemd

## Files Created/Modified

### New Files (12):
- `install_autostart.sh` (executable)
- `uninstall_autostart.sh` (executable)
- `start_medical_inventory.sh` (executable)
- `medical-inventory.service` (systemd template)
- `test_autostart_setup.sh` (executable)
- `RASPBERRY_PI_SETUP.md` (documentation)
- `AUTOSTART_SETUP.md` (documentation)
- `QUICK_START_AUTOBOOT.md` (documentation)
- `AUTO_START_SUMMARY.md` (this file)
- `.gitignore` (git configuration)

### Modified Files (1):
- `README.md` (updated with auto-start and Pi 4 info)

### Unchanged Files:
- `medical_inventory.py` (main application - no changes)
- `facial_recognition.py` (face detection - no changes)
- `db_manager.py` (database - no changes)
- All test files (no changes)
- `requirements.txt` (no changes)

## Security Considerations

1. **Physical Security**: Secure the Raspberry Pi in a locked enclosure
2. **User Permissions**: Service runs as regular user, not root
3. **Camera Access**: User must be in `video` group
4. **Network**: Configure firewall if network-accessible
5. **Updates**: Regular system and package updates recommended
6. **Backups**: Automated database backups via cron

## Troubleshooting

### Service Won't Start
```bash
sudo journalctl -u medical-inventory@$USER.service -b
```

### Camera Issues
```bash
sudo usermod -a -G video $USER
# Log out and back in
```

### Display Issues
```bash
# Check DISPLAY variable in service file
sudo systemctl edit medical-inventory@.service --full
```

### Performance Issues
- Increase GPU memory: Edit `/boot/config.txt` → `gpu_mem=256`
- Enable overclocking: `sudo raspi-config` → Performance Options
- Reduce frame processing rate in `facial_recognition.py`

## Support & Documentation

- **Main README**: [README.md](README.md)
- **Quick Start**: [QUICK_START_AUTOBOOT.md](QUICK_START_AUTOBOOT.md)
- **Detailed Auto-Start**: [AUTOSTART_SETUP.md](AUTOSTART_SETUP.md)
- **Raspberry Pi 4 Setup**: [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md)
- **Repository**: https://github.com/DylanSoule/Medical-Inventory-System-NASA-Hunch-25-26
- **NASA Hunch**: https://nasahunch.com/

## Testing

Run the validation script:
```bash
./test_autostart_setup.sh
```

All tests should pass before deployment.

## Deployment Checklist

- [ ] Raspberry Pi 4 hardware assembled
- [ ] Raspberry Pi OS installed and updated
- [ ] Dependencies installed
- [ ] Camera and barcode scanner tested
- [ ] Facial recognition references configured
- [ ] Application tested manually
- [ ] Auto-start installed (`sudo ./install_autostart.sh`)
- [ ] Auto-login configured (`sudo raspi-config`)
- [ ] Screen blanking disabled
- [ ] System tested with reboot
- [ ] Backup created
- [ ] Physical security in place
- [ ] User training completed

## Success Criteria

The system is successfully configured when:

1. ✓ Raspberry Pi 4 boots automatically to the Medical Inventory System
2. ✓ Application runs in fullscreen without manual intervention
3. ✓ Camera and barcode scanner are accessible
4. ✓ Facial recognition works properly
5. ✓ Service restarts automatically on failure
6. ✓ Logs are accessible for troubleshooting
7. ✓ System can be managed via systemctl commands

## Conclusion

The Medical Inventory System is now a **bootable kiosk system** optimized for **Raspberry Pi 4**. The system automatically starts on boot, requires no manual intervention, and is ready for deployment in medical facilities, space stations, or long-term space missions.

For questions or issues, refer to the documentation files or contact the development team (see README.md).
