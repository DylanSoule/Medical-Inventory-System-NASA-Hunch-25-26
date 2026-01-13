# Quick Start: Auto-Boot Configuration

This is a quick reference for setting up the Medical Inventory System to start automatically on boot on **Raspberry Pi 4**.

## Installation (3 Steps)

### 1. Install Dependencies
```bash
cd ~/Medical-Inventory-System-NASA-Hunch-25-26
pip install -r requirements.txt
```

### 2. Test the Application
```bash
python3 src/medical_inventory.py
```
Press F11 to toggle fullscreen, Escape to exit fullscreen.

### 3. Enable Auto-Start
```bash
sudo ./scripts/install_autostart.sh
```

That's it! The system will now start automatically on boot.

## Common Commands

| Command | Description |
|---------|-------------|
| `sudo systemctl start medical-inventory@$USER.service` | Start service now |
| `sudo systemctl stop medical-inventory@$USER.service` | Stop service |
| `sudo systemctl status medical-inventory@$USER.service` | Check status |
| `sudo journalctl -u medical-inventory@$USER.service -f` | View live logs |
| `sudo ./scripts/uninstall_autostart.sh` | Remove auto-start |

## Raspberry Pi 4 Kiosk Setup

For a dedicated Raspberry Pi 4 kiosk system:

1. **Enable auto-login:**
   ```bash
   sudo raspi-config
   # System Options → Boot / Auto Login → Desktop Autologin
   ```

2. **Disable screen blanking:**
   ```bash
   echo "@xset s noblank" >> ~/.config/lxsession/LXDE-pi/autostart
   echo "@xset s off" >> ~/.config/lxsession/LXDE-pi/autostart
   echo "@xset -dpms" >> ~/.config/lxsession/LXDE-pi/autostart
   ```

3. **Reboot:**
   ```bash
   sudo reboot
   ```

## Troubleshooting

### Service won't start
```bash
sudo journalctl -u medical-inventory@$USER.service -n 50
```

### Camera issues
```bash
sudo usermod -a -G video $USER
# Then log out and back in
```

### Application crashes
```bash
cat ~/Medical-Inventory-System-NASA-Hunch-25-26/startup.log
```

## Full Documentation

- **Auto-Start Details**: [AUTOSTART_SETUP.md](AUTOSTART_SETUP.md)
- **Complete Raspberry Pi 4 Setup**: [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md)
