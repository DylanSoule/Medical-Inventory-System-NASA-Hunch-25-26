#!/bin/bash
# Uninstallation script for Medical Inventory System auto-start
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

SERVICE_FILE="/etc/systemd/system/medical-inventory@.service"

echo "Uninstalling Medical Inventory System auto-start for user: $ACTUAL_USER"

# Stop the service if it's running
if systemctl is-active --quiet "medical-inventory@$ACTUAL_USER.service"; then
    echo "Stopping service..."
    systemctl stop "medical-inventory@$ACTUAL_USER.service"
fi

# Disable the service
if systemctl is-enabled --quiet "medical-inventory@$ACTUAL_USER.service" 2>/dev/null; then
    echo "Disabling service..."
    systemctl disable "medical-inventory@$ACTUAL_USER.service"
fi

# Remove the service file
if [ -f "$SERVICE_FILE" ]; then
    echo "Removing service file..."
    rm "$SERVICE_FILE"
    systemctl daemon-reload
fi

echo ""
echo "✓ Medical Inventory System auto-start has been uninstalled"
echo "The application will no longer start automatically on boot"
