#!/bin/bash
#
# Launcher script for Medical Inventory System (Kivy Version)
# NASA HUNCH Project 2025-26
#

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Set environment variables for optimal Kivy performance
export KIVY_WINDOW=sdl2
export KIVY_GL_BACKEND=gl

# Change to project root
cd "$PROJECT_ROOT"

# Check if running on Raspberry Pi
if grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "Detected Raspberry Pi - Using optimized settings"
    export KIVY_METRICS_DENSITY=1.5
fi

# Run the application
echo "Starting Medical Inventory System (Kivy)..."
python3 src/medical_inventory_kivy.py "$@"
