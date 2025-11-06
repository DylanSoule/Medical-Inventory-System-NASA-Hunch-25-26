# Auto-Start Setup Guide

This guide explains how to configure the Medical Inventory System to start automatically when your Raspberry Pi (or other Linux system) boots up, creating a dedicated kiosk-like system.

## Overview

The auto-start system uses systemd services to launch the Medical Inventory System automatically when the system boots into the graphical environment. This is ideal for dedicated medical inventory stations that should be ready to use immediately upon power-up.

## Prerequisites

Before setting up auto-start, ensure:

1. The Medical Inventory System is fully installed and working
2. All dependencies are installed (see main README.md)
3. You have tested the application manually and it runs correctly
4. You have set up facial recognition references (if using that feature)
5. You have sudo/administrator access to the system

## Quick Installation

### 1. Install Auto-Start

From the project directory, run:

```bash
sudo ./scripts/install_autostart.sh
```

This script will:
- Create a systemd service for the Medical Inventory System
- Configure it to start automatically on boot
- Set up proper permissions and environment variables

### 2. Test the Installation

Start the service immediately to test it:

```bash
sudo systemctl start medical-inventory@$USER.service
```

Check if it's running:

```bash
sudo systemctl status medical-inventory@$USER.service
```

### 3. Reboot to Verify

Reboot your system to ensure the application starts automatically:

```bash
sudo reboot
```

After reboot, the Medical Inventory System should start automatically and appear in fullscreen mode.

## Management Commands

### Start the Service
```bash
sudo systemctl start medical-inventory@$USER.service
```

### Stop the Service
```bash
sudo systemctl stop medical-inventory@$USER.service
```

### Restart the Service
```bash
sudo systemctl restart medical-inventory@$USER.service
```

### Check Service Status
```bash
sudo systemctl status medical-inventory@$USER.service
```

### View Live Logs
```bash
sudo journalctl -u medical-inventory@$USER.service -f
```

### View All Logs
```bash
sudo journalctl -u medical-inventory@$USER.service
```

### Disable Auto-Start (without uninstalling)
```bash
sudo systemctl disable medical-inventory@$USER.service
```

### Re-enable Auto-Start
```bash
sudo systemctl enable medical-inventory@$USER.service
```

## Uninstallation

To completely remove the auto-start configuration:

```bash
sudo ./scripts/uninstall_autostart.sh
```

This will:
- Stop the service if running
- Disable auto-start
- Remove the systemd service file

The application itself will remain installed and can still be run manually.

## Raspberry Pi Specific Configuration

### Auto-Login Setup

For a true kiosk experience, configure auto-login on your Raspberry Pi:

1. Run the Raspberry Pi configuration tool:
   ```bash
   sudo raspi-config
   ```

2. Navigate to: **System Options** → **Boot / Auto Login** → **Desktop Autologin**

3. Select your user account

4. Reboot

### Hide Mouse Cursor (Optional)

For a cleaner kiosk interface, you can hide the mouse cursor:

1. Install unclutter:
   ```bash
   sudo apt-get install unclutter
   ```

2. Add to auto-start by creating `~/.config/autostart/unclutter.desktop`:
   ```desktop
   [Desktop Entry]
   Type=Application
   Name=Unclutter
   Exec=unclutter -idle 0.1
   ```

### Disable Screen Blanking

To prevent the screen from turning off:

1. Edit `/etc/lightdm/lightdm.conf`:
   ```bash
   sudo nano /etc/lightdm/lightdm.conf
   ```

2. Add under `[Seat:*]`:
   ```
   xserver-command=X -s 0 -dpms
   ```

3. Or create `~/.config/lxsession/LXDE-pi/autostart`:
   ```
   @xset s noblank
   @xset s off
   @xset -dpms
   ```

## Troubleshooting

### Service Won't Start

Check the logs for errors:
```bash
sudo journalctl -u medical-inventory@$USER.service -n 50
```

Common issues:
- Missing dependencies: Ensure all Python packages are installed
- Camera not detected: Check camera connection and permissions
- Display not available: Ensure X server is running

### Application Starts But Crashes

Check the application-specific logs:
```bash
cat ~/Medical-Inventory-System-NASA-Hunch-25-26/startup.log
```

### Camera Permission Issues

Add your user to the video group:
```bash
sudo usermod -a -G video $USER
```

Then log out and back in.

### Display Issues

Ensure DISPLAY environment variable is set correctly. The default is `:0`. If your system uses a different display, edit the service file:

```bash
sudo systemctl edit medical-inventory@.service
```

Add:
```
[Service]
Environment=DISPLAY=:1
```

Replace `:1` with your display number.

## Advanced Configuration

### Running on a Different Port/Display

If you need to customize the display or other environment variables, edit the service file:

```bash
sudo systemctl edit medical-inventory@.service --full
```

### Using a Virtual Environment

If you're using a Python virtual environment, the startup script will automatically detect and activate a `venv` directory in the project folder. To use this:

1. Create a virtual environment:
   ```bash
   cd ~/Medical-Inventory-System-NASA-Hunch-25-26
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. The startup script will automatically use this environment

### Custom Startup Script

If you need custom initialization logic, edit `start_medical_inventory.sh` before running the installation script.

## Creating a Dedicated Kiosk System

For maximum security and reliability, consider these additional steps:

1. **Create a dedicated user account** for the kiosk
2. **Disable WiFi/Bluetooth** if not needed
3. **Remove unnecessary software** to reduce attack surface
4. **Set up read-only filesystem** to prevent unauthorized changes
5. **Configure automatic updates** for security patches
6. **Set up remote monitoring** to track system health

## OS Image Creation (Advanced)

To create a bootable OS image with the Medical Inventory System pre-configured:

1. Set up a Raspberry Pi with all configurations
2. Install and configure the auto-start system
3. Use tools like `rpi-clone` or `dd` to create an image
4. Distribute the image for deployment on multiple devices

Example using dd:
```bash
# On another Linux system with SD card inserted
sudo dd if=/dev/sdX of=medical-inventory-system.img bs=4M status=progress
```

Replace `/dev/sdX` with your SD card device.

## Support

For issues or questions:
- Check the main README.md
- Review system logs
- Contact the development team (see main README.md for contact info)
