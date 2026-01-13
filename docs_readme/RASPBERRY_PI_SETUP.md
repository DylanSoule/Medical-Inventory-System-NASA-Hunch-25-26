# Raspberry Pi 4 Setup Guide

Complete setup guide for deploying the Medical Inventory System on a Raspberry Pi 4 as a dedicated kiosk system.

## Hardware Requirements

- **Raspberry Pi 4** (2GB RAM minimum, 4GB+ recommended)
- **MicroSD Card** (16GB minimum, 32GB+ recommended, Class 10 or UHS-I)
- **Official Raspberry Pi Power Supply** (5V 3A USB-C)
- **USB Webcam or Raspberry Pi Camera Module v2/v3**
- **USB Barcode Scanner** (configured as HID keyboard input device)
- **Display** (HDMI-compatible monitor or touchscreen)
- **Keyboard** (for initial setup only)
- Optional: **Mouse** (for initial setup only)
- Optional: **Cooling** (heatsinks or fan for sustained operation)

## Software Requirements

- **Raspberry Pi OS** (64-bit recommended for better performance)
  - Raspberry Pi OS with Desktop (for GUI applications)
  - Based on Debian Bullseye or newer

## Initial Raspberry Pi Setup

### 1. Prepare the SD Card

Download and install the **Raspberry Pi Imager**: https://www.raspberrypi.com/software/

1. Insert your microSD card into your computer
2. Open Raspberry Pi Imager
3. Choose OS: **Raspberry Pi OS (64-bit)** with Desktop
4. Choose Storage: Select your microSD card
5. Click the gear icon (⚙️) for advanced options:
   - Set hostname: `medical-inventory` (or your preference)
   - Enable SSH (optional, for remote access)
   - Set username and password
   - Configure WiFi (if needed)
   - Set locale settings
6. Click **Write** and wait for completion

### 2. First Boot Configuration

1. Insert the microSD card into your Raspberry Pi 4
2. Connect display, keyboard, and power
3. Wait for first boot (may take a few minutes)
4. Complete the setup wizard if it appears

### 3. Update the System

Open a terminal and run:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git python3-pip python3-tk python3-dev
```

This may take 10-20 minutes depending on your internet connection.

### 4. Install Additional Dependencies

```bash
# Install OpenCV dependencies
sudo apt install -y libopencv-dev python3-opencv

# Install build tools for Python packages
sudo apt install -y build-essential cmake pkg-config

# Install image processing libraries
sudo apt install -y libjpeg-dev libtiff5-dev libpng-dev
sudo apt install -y libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
sudo apt install -y libxvidcore-dev libx264-dev

# Install GUI dependencies
sudo apt install -y libgtk-3-dev libcanberra-gtk3-module

# Install utilities
sudo apt install -y unclutter xdotool
```

## Application Installation

### 1. Clone the Repository

```bash
cd ~
git clone https://github.com/DylanSoule/Medical-Inventory-System-NASA-Hunch-25-26.git
cd Medical-Inventory-System-NASA-Hunch-25-26
```

### 2. Install Python Dependencies

```bash
# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install --upgrade pip
pip install -r requirements.txt

# For Raspberry Pi, you may need to install some packages separately
pip install numpy opencv-python insightface onnxruntime
```

**Note:** Installing insightface and onnxruntime on Raspberry Pi may take 15-30 minutes.

### 3. Set Up Camera Permissions

```bash
sudo usermod -a -G video $USER
```

Log out and back in for this to take effect.

### 4. Configure Facial Recognition

```bash
# Create references directory
mkdir -p assets/references

# Add reference images (replace with your actual images)
# Copy facial reference images to the assets/references/ directory
# Use clear, forward-facing photos with consistent lighting
```

### 5. Test the Application

```bash
python3 src/medical_inventory.py
```

- Press **F11** to toggle fullscreen
- Press **Escape** to exit fullscreen
- Press **Ctrl+C** in terminal to quit

If the application works correctly, proceed to auto-start configuration.

## Auto-Start Configuration

### 1. Install Auto-Start Service

```bash
cd ~/Medical-Inventory-System-NASA-Hunch-25-26
sudo ./scripts/install_autostart.sh
```

### 2. Configure Auto-Login

For the system to start automatically without requiring login:

```bash
sudo raspi-config
```

Navigate through:
- **System Options** → **Boot / Auto Login** → **Desktop Autologin**
- Select your user account
- Finish and reboot

### 3. Disable Screen Blanking

Create or edit the autostart file:

```bash
mkdir -p ~/.config/lxsession/LXDE-pi
nano ~/.config/lxsession/LXDE-pi/autostart
```

Add these lines:

```
@xset s noblank
@xset s off
@xset -dpms
```

Save with **Ctrl+O**, **Enter**, then exit with **Ctrl+X**.

### 4. Hide Mouse Cursor (Optional)

```bash
sudo apt install -y unclutter
```

Add to autostart:
```bash
echo "@unclutter -idle 0.1 -root" >> ~/.config/lxsession/LXDE-pi/autostart
```

### 5. Set Static Display Configuration (Optional)

For consistent display settings, edit config.txt:

```bash
sudo nano /boot/config.txt
```

Add or modify these settings:

```
# Force HDMI output
hdmi_force_hotplug=1

# Set display resolution (adjust to your display)
hdmi_group=2
hdmi_mode=82

# Rotate display if needed (0=normal, 1=90, 2=180, 3=270)
display_rotate=0
```

Reboot to apply changes.

## Performance Optimization for Raspberry Pi 4

### 1. Increase GPU Memory

```bash
sudo nano /boot/config.txt
```

Add or modify:
```
gpu_mem=256
```

This allocates 256MB to GPU, improving graphics performance.

### 2. Enable Hardware Acceleration

Already enabled by default on Raspberry Pi 4 with recent OS versions.

### 3. Optimize Python Performance

The application automatically uses CPU execution for ONNX Runtime, which is optimal for Raspberry Pi 4.

### 4. Reduce Startup Time

Disable unnecessary services:

```bash
# Disable Bluetooth (if not needed)
sudo systemctl disable bluetooth.service

# Disable WiFi power management
sudo iw wlan0 set power_save off
```

## Troubleshooting

### Camera Not Detected

```bash
# Check if camera is detected
ls -l /dev/video*

# Test camera with cheese or fswebcam
sudo apt install cheese
cheese
```

For **Raspberry Pi Camera Module**:

```bash
# Enable camera interface
sudo raspi-config
# Interface Options → Legacy Camera → Enable

# Reboot
sudo reboot
```

### Application Slow or Laggy

1. **Reduce frame processing rate** - Edit `facial_recognition.py`:
   ```python
   # Change line ~177 from:
   if frame_count % 75 == 0 and frame_queue.empty():
   # To a higher number for slower processing:
   if frame_count % 100 == 0 and frame_queue.empty():
   ```

2. **Enable overclocking** (carefully):
   ```bash
   sudo raspi-config
   # Performance Options → Overclock → Modest or Medium
   ```
   
   **Warning:** Ensure adequate cooling before overclocking.

### Service Won't Start on Boot

Check logs:
```bash
sudo journalctl -u medical-inventory@$USER.service -b
```

Common issues:
- Camera not ready: Increase startup delay in `start_medical_inventory.sh`
- Display server not ready: Wait longer for X server
- Permission issues: Check user is in video group

### Out of Memory Errors

Monitor memory usage:
```bash
free -h
```

If running low on memory:
1. Close other applications
2. Consider upgrading to 4GB or 8GB Raspberry Pi 4
3. Reduce image processing resolution in the code

### Touch Screen Not Working

```bash
# Install touchscreen drivers
sudo apt install -y xserver-xorg-input-evdev

# Create config file
sudo nano /usr/share/X11/xorg.conf.d/45-evdev.conf
```

Add:
```
Section "InputClass"
    Identifier "evdev touchscreen catchall"
    MatchIsTouchscreen "on"
    MatchDevicePath "/dev/input/event*"
    Driver "evdev"
EndSection
```

## Network Configuration

### Static IP Address

For reliable remote access:

```bash
sudo nmtui
# Or manually edit /etc/dhcpcd.conf
```

### SSH Access

Enable SSH for remote management:

```bash
sudo systemctl enable ssh
sudo systemctl start ssh
```

## Backup and Recovery

### Create System Backup

After successful setup:

```bash
# On another Linux computer with SD card reader
sudo dd if=/dev/sdX of=medical-inventory-backup.img bs=4M status=progress
```

### Database Backups

Schedule automatic database backups:

```bash
# Create backup script
nano ~/backup_inventory.sh
```

Add:
```bash
#!/bin/bash
DB_PATH=~/Medical-Inventory-System-NASA-Hunch-25-26/inventory.db
BACKUP_DIR=~/inventory_backups
mkdir -p $BACKUP_DIR
cp $DB_PATH $BACKUP_DIR/inventory_$(date +%Y%m%d_%H%M%S).db
# Keep only last 30 days
find $BACKUP_DIR -name "inventory_*.db" -mtime +30 -delete
```

Make executable and add to crontab:
```bash
chmod +x ~/backup_inventory.sh
crontab -e
# Add line:
0 0 * * * ~/backup_inventory.sh
```

## Security Recommendations

1. **Change default password** - Use a strong password
2. **Update regularly** - `sudo apt update && sudo apt upgrade`
3. **Firewall** - Configure UFW if network-accessible
4. **Physical security** - Secure the device in a locked enclosure
5. **Disable SSH** if not needed for remote access
6. **Regular backups** - Automate database and system backups

## Maintenance

### Regular Updates

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Update Python packages
source ~/Medical-Inventory-System-NASA-Hunch-25-26/venv/bin/activate
pip install --upgrade pip
pip install --upgrade -r requirements.txt
```

### Monitor System Health

```bash
# Check temperature
vcgencmd measure_temp

# Check memory
free -h

# Check disk space
df -h

# Check service status
sudo systemctl status medical-inventory@$USER.service
```

### Logs Rotation

Prevent log files from filling the SD card:

```bash
sudo nano /etc/logrotate.d/medical-inventory
```

Add:
```
/home/*/Medical-Inventory-System-NASA-Hunch-25-26/startup.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

## Deployment Checklist

- [ ] Raspberry Pi 4 hardware assembled with cooling
- [ ] Raspberry Pi OS installed and updated
- [ ] All dependencies installed
- [ ] Camera and barcode scanner connected and tested
- [ ] Application installed and tested manually
- [ ] Facial recognition references configured
- [ ] Auto-start service installed and tested
- [ ] Auto-login configured
- [ ] Screen blanking disabled
- [ ] Mouse cursor hidden (if desired)
- [ ] Static IP configured (if needed)
- [ ] System backup created
- [ ] Database backup automated
- [ ] Physical security in place
- [ ] User training completed

## Support Resources

- **Raspberry Pi Documentation**: https://www.raspberrypi.com/documentation/
- **Project Repository**: https://github.com/DylanSoule/Medical-Inventory-System-NASA-Hunch-25-26
- **Raspberry Pi Forums**: https://forums.raspberrypi.com/
- **Project Team**: See main README.md for contact information

## Common Commands Quick Reference

```bash
# Start service manually
sudo systemctl start medical-inventory@$USER.service

# Stop service
sudo systemctl stop medical-inventory@$USER.service

# View logs
sudo journalctl -u medical-inventory@$USER.service -f

# Check temperature
vcgencmd measure_temp

# Reboot
sudo reboot

# Shutdown
sudo shutdown -h now

# Test camera
python3 -c "import cv2; print('OpenCV:', cv2.__version__); cap=cv2.VideoCapture(0); print('Camera:', cap.isOpened()); cap.release()"
```
