#!/bin/bash
# Startup script for Medical Inventory System
# This script ensures the proper environment is set before launching the application

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Set display for GUI
export DISPLAY=${DISPLAY:-:0}

# Change to the project directory
cd "$PROJECT_DIR"

# Activate virtual environment if it exists
if [ -d "$PROJECT_DIR/venv" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
fi

# Wait for X server to be ready (important for auto-start)
echo "Waiting for X server..."
X_READY=false
for i in {1..30}; do
    if xset q &>/dev/null; then
        echo "X server is ready"
        X_READY=true
        break
    fi
    sleep 1
done

if [ "$X_READY" = false ]; then
    echo "ERROR: X server did not become available after 30 seconds" >&2
    echo "Check if graphical environment is running" >&2
    exit 1
fi

# Start the database container
echo "Starting Docker container..."
docker start medical-inventory-db 2>/dev/null || echo "WARNING: Could not start medical-inventory-db container"

# Give the database a moment to accept connections
sleep 2

# Launch the application
echo "Starting Medical Inventory System..."
python3 "$PROJECT_DIR/src/medical_inventory.py"

# If the application exits, log it
echo "Medical Inventory System stopped at $(date)" >> "$SCRIPT_DIR/startup.log"
