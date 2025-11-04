#!/bin/bash
# Installation script for auto-starting Medical Inventory System on boot
# This script should be run with sudo

set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run this script with sudo"
    exit 1
fi

# Get the actual user (not root when using sudo)
ACTUAL_USER="${SUDO_USER:-$USER}"
if [ "$ACTUAL_USER" = "root" ]; then
    echo "Please run this script using sudo as a regular user"
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing Medical Inventory System auto-start for user: $ACTUAL_USER"
echo "Application directory: $SCRIPT_DIR"

# Make the startup script executable
chmod +x "$SCRIPT_DIR/start_medical_inventory.sh"

# Create systemd service file with proper user paths
SERVICE_FILE="/etc/systemd/system/medical-inventory@.service"
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Medical Inventory System for NASA Hunch
After=graphical.target
Wants=graphical.target

[Service]
Type=simple
User=%i
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/%i/.Xauthority
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/start_medical_inventory.sh
Restart=on-failure
RestartSec=5

[Install]
WantedBy=graphical.target
EOF

echo "Created systemd service file at $SERVICE_FILE"

# Enable the service for the current user
systemctl enable "medical-inventory@$ACTUAL_USER.service"

echo ""
echo "✓ Medical Inventory System has been configured to start automatically on boot"
echo ""
echo "Management commands:"
echo "  Start now:    sudo systemctl start medical-inventory@$ACTUAL_USER.service"
echo "  Stop:         sudo systemctl stop medical-inventory@$ACTUAL_USER.service"
echo "  Check status: sudo systemctl status medical-inventory@$ACTUAL_USER.service"
echo "  View logs:    sudo journalctl -u medical-inventory@$ACTUAL_USER.service -f"
echo "  Disable:      sudo systemctl disable medical-inventory@$ACTUAL_USER.service"
echo ""
echo "The system will start automatically on next boot."
echo "To start it now, run: sudo systemctl start medical-inventory@$ACTUAL_USER.service"
