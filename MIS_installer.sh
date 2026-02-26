#!/bin/bash
# =============================================================
# Medical Inventory System — One-Step Installer
# Run:  sudo bash MIS_installer.sh
# =============================================================
set -e

# ── Pre-flight checks ──────────────────────────────────────
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Please run this installer with sudo"
    echo "  Usage:  sudo bash $0"
    exit 1
fi

ACTUAL_USER="${SUDO_USER:-$USER}"
if [ "$ACTUAL_USER" = "root" ]; then
    echo "ERROR: Run this script via sudo as a regular user, not as root directly."
    exit 1
fi

ACTUAL_HOME=$(eval echo "~$ACTUAL_USER")
WORKSPACE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_URL="https://github.com/NASA-Hunch/Medical-Inventory-System-NASA-Hunch-25-26.git"

# If the installer is inside the repo, use that directly
if [ -d "$WORKSPACE/.git" ]; then
    REPO_DIR="$WORKSPACE"
else
    REPO_DIR="$WORKSPACE/Medical-Inventory-System-NASA-Hunch-25-26"
fi

echo "============================================="
echo " Medical Inventory System Installer"
echo "============================================="
echo "User       : $ACTUAL_USER"
echo "Home       : $ACTUAL_HOME"
echo "Workspace  : $WORKSPACE"
echo "Repo dir   : $REPO_DIR"
echo "============================================="
echo ""

# ── Helper: run a command as the real user ──────────────────
run_as_user() {
    sudo -u "$ACTUAL_USER" -- "$@"
}

# ── 1. Install system dependencies ─────────────────────────
echo ">>> [1/7] Installing system dependencies..."
apt-get update -qq

PACKAGES=(
    git
    python3
    python3-pip
    python3-venv
    docker.io
    docker-compose
    xdotool          # useful for X checks
)

for pkg in "${PACKAGES[@]}"; do
    if dpkg -s "$pkg" &>/dev/null; then
        echo "  ✓ $pkg already installed"
    else
        echo "  Installing $pkg ..."
        apt-get install -y -qq "$pkg"
    fi
done

# ── 2. Enable & start Docker ───────────────────────────────
echo ""
echo ">>> [2/7] Configuring Docker..."
systemctl enable docker
systemctl start docker

# Add user to docker group so the startup script can call docker
if id -nG "$ACTUAL_USER" | grep -qw docker; then
    echo "  ✓ $ACTUAL_USER is already in the docker group"
else
    echo "  Adding $ACTUAL_USER to docker group..."
    usermod -aG docker "$ACTUAL_USER"
    echo "  (Group change takes effect on next login or reboot)"
fi

# ── 3. Clone or update the repository ──────────────────────
echo ""
echo ">>> [3/7] Setting up repository..."
if [ -d "$REPO_DIR/.git" ]; then
    echo "  ✓ Repository already exists at $REPO_DIR — skipping clone"
else
    echo "  Cloning repository..."
    run_as_user git clone "$REPO_URL" "$REPO_DIR"
fi

# ── 4. Python virtual-environment & dependencies ───────────
echo ""
echo ">>> [4/7] Setting up Python virtual environment..."
VENV_DIR="$REPO_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    run_as_user python3 -m venv "$VENV_DIR"
fi

# Install requirements if the file exists
if [ -f "$REPO_DIR/requirements.txt" ]; then
    echo "  Installing Python dependencies..."
    run_as_user "$VENV_DIR/bin/pip" install --upgrade pip -q
    run_as_user "$VENV_DIR/bin/pip" install -r "$REPO_DIR/requirements.txt" -q
    echo "  ✓ Python dependencies installed"
else
    echo "  ⚠ No requirements.txt found — skipping pip install"
fi

# ── 5. Set up the database Docker container ─────────────────
echo ""
echo ">>> [5/7] Setting up database container..."
if docker ps -a --format '{{.Names}}' | grep -q '^medical-inventory-db$'; then
    echo "  ✓ Container 'medical-inventory-db' already exists"
else
    # If a docker-compose file exists, use it; otherwise create a basic container
    if [ -f "$REPO_DIR/docker-compose.yml" ] || [ -f "$REPO_DIR/docker-compose.yaml" ]; then
        echo "  Starting containers with docker-compose..."
        (cd "$REPO_DIR" && docker-compose up -d)
    else
        echo "  Creating default PostgreSQL container..."
        docker run -d \
            --name medical-inventory-db \
            -e POSTGRES_USER=medinv \
            -e POSTGRES_PASSWORD=medinv \
            -e POSTGRES_DB=medical_inventory \
            -p 5432:5432 \
            --restart unless-stopped \
            postgres:16-alpine
    fi
fi
echo "  ✓ Database container ready"

# ── 6. Make scripts executable ──────────────────────────────
echo ""
echo ">>> [6/7] Setting file permissions..."
chmod +x "$REPO_DIR/scripts/start_medical_inventory.sh"
chmod +x "$REPO_DIR/scripts/install_autostart.sh"
echo "  ✓ Scripts are executable"

# ── 7. Install the systemd auto-start service ──────────────
echo ""
echo ">>> [7/7] Installing auto-start service..."
bash "$REPO_DIR/scripts/install_autostart.sh"

# ── Done! ───────────────────────────────────────────────────
echo ""
echo "============================================="
echo " Installation Complete!"
echo "============================================="
echo ""
echo "The Medical Inventory System will start"
echo "automatically on the next boot."
echo ""
read -rp "Would you like to start it now? [y/N] " START_NOW
if [[ "$START_NOW" =~ ^[Yy]$ ]]; then
    echo "Starting service..."
    systemctl start "medical-inventory@$ACTUAL_USER.service"
    echo "✓ Service started. Check status with:"
    echo "  sudo systemctl status medical-inventory@$ACTUAL_USER.service"
else
    echo "You can start it later with:"
    echo "  sudo systemctl start medical-inventory@$ACTUAL_USER.service"
fi
echo ""
echo "Useful commands:"
echo "  Status : sudo systemctl status medical-inventory@$ACTUAL_USER.service"
echo "  Logs   : sudo journalctl -u medical-inventory@$ACTUAL_USER.service -f"
echo "  Stop   : sudo systemctl stop medical-inventory@$ACTUAL_USER.service"
echo "  Disable: sudo systemctl disable medical-inventory@$ACTUAL_USER.service"
echo ""