#!/bin/bash
# Test script to validate auto-start setup files
# This does not require sudo and only validates the files are correct

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

echo "=== Testing Auto-Start Setup Files ==="
echo ""

# Test 1: Check all required files exist
echo "Test 1: Checking required files exist..."
REQUIRED_FILES=(
    "scripts/start_medical_inventory.sh"
    "scripts/install_autostart.sh"
    "scripts/uninstall_autostart.sh"
    "scripts/medical-inventory.service"
    "docs/AUTOSTART_SETUP.md"
    "docs/QUICK_START_AUTOBOOT.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file exists"
    else
        echo "  ✗ $file missing"
        exit 1
    fi
done
echo ""

# Test 2: Check scripts are executable
echo "Test 2: Checking scripts are executable..."
EXEC_FILES=(
    "scripts/start_medical_inventory.sh"
    "scripts/install_autostart.sh"
    "scripts/uninstall_autostart.sh"
)

for file in "${EXEC_FILES[@]}"; do
    if [ -x "$file" ]; then
        echo "  ✓ $file is executable"
    else
        echo "  ✗ $file is not executable"
        exit 1
    fi
done
echo ""

# Test 3: Validate shell script syntax
echo "Test 3: Validating shell script syntax..."
for file in "${EXEC_FILES[@]}"; do
    if bash -n "$file" 2>/dev/null; then
        echo "  ✓ $file syntax is valid"
    else
        echo "  ✗ $file has syntax errors"
        exit 1
    fi
done
echo ""

# Test 4: Check systemd service file format
echo "Test 4: Checking systemd service file format..."
if grep -q "\[Unit\]" scripts/medical-inventory.service && \
   grep -q "\[Service\]" scripts/medical-inventory.service && \
   grep -q "\[Install\]" scripts/medical-inventory.service; then
    echo "  ✓ Service file has correct sections"
else
    echo "  ✗ Service file is missing required sections"
    exit 1
fi
echo ""

# Test 5: Check if main application exists
echo "Test 5: Checking main application file..."
if [ -f "src/medical_inventory.py" ]; then
    echo "  ✓ src/medical_inventory.py exists"
else
    echo "  ✗ src/medical_inventory.py missing"
    exit 1
fi
echo ""

# Test 6: Check documentation completeness
echo "Test 6: Checking documentation..."
if grep -q "Auto-Start Configuration" README.md; then
    echo "  ✓ README.md includes auto-start section"
else
    echo "  ✗ README.md missing auto-start section"
    exit 1
fi

if grep -q "sudo ./scripts/install_autostart.sh\|sudo ./install_autostart.sh" docs/AUTOSTART_SETUP.md; then
    echo "  ✓ AUTOSTART_SETUP.md includes installation instructions"
else
    echo "  ✗ AUTOSTART_SETUP.md missing installation instructions"
    exit 1
fi
echo ""

# Test 7: Check .gitignore
echo "Test 7: Checking .gitignore..."
if [ -f ".gitignore" ]; then
    if grep -q '^\*\.log' .gitignore && grep -q "venv/" .gitignore; then
        echo "  ✓ .gitignore exists and contains expected patterns"
    else
        echo "  ✗ .gitignore missing expected patterns"
        exit 1
    fi
else
    echo "  ✗ .gitignore missing"
    exit 1
fi
echo ""

echo "=== All Tests Passed ==="
echo ""
echo "Auto-start setup files are valid and ready for use."
echo "To install auto-start, run: sudo ./scripts/install_autostart.sh"
