#!/bin/bash
# Startup script for Medical Inventory System
# This script ensures the proper environment is set before launching the application

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set display for GUI
export DISPLAY=${DISPLAY:-:0}

# Change to the application directory
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Wait for X server to be ready (important for auto-start)
echo "Waiting for X server..."
for i in {1..30}; do
    if xset q &>/dev/null; then
        echo "X server is ready"
        break
    fi
    sleep 1
done

# Launch the application
echo "Starting Medical Inventory System..."
python3 medical_inventory.py

# If the application exits, log it
echo "Medical Inventory System stopped at $(date)" >> "$SCRIPT_DIR/startup.log"
