#!/bin/bash
# GST Filing - Linux/Mac Installer
set -e

echo "============================================"
echo " GST Filing - Setup (Linux/Mac)"
echo "============================================"
echo ""

# ── Detect package manager ──────────────────────
if command -v apt-get &>/dev/null; then
    PKG="apt"
elif command -v dnf &>/dev/null; then
    PKG="dnf"
elif command -v brew &>/dev/null; then
    PKG="brew"
else
    echo "ERROR: No supported package manager found (apt / dnf / brew)."
    echo "Install Python 3.11+, Node.js 18+, and Git manually, then re-run this script."
    exit 1
fi

echo "Package manager: $PKG"
echo ""

# ── Install Git ─────────────────────────────────
echo "[1/3] Checking Git..."
if ! command -v git &>/dev/null; then
    echo "  Installing Git..."
    if [ "$PKG" = "apt" ];  then sudo apt-get install -y git
    elif [ "$PKG" = "dnf" ]; then sudo dnf install -y git
    elif [ "$PKG" = "brew" ]; then brew install git
    fi
else
    echo "  Git $(git --version) already installed."
fi
echo ""

# ── Install Python ──────────────────────────────
echo "[2/3] Checking Python..."
if ! command -v python3 &>/dev/null; then
    echo "  Installing Python..."
    if [ "$PKG" = "apt" ];  then sudo apt-get install -y python3 python3-pip python3-venv
    elif [ "$PKG" = "dnf" ]; then sudo dnf install -y python3 python3-pip
    elif [ "$PKG" = "brew" ]; then brew install python
    fi
else
    echo "  $(python3 --version) already installed."
fi
echo ""

# ── Install Node.js ─────────────────────────────
echo "[3/3] Checking Node.js..."
if ! command -v node &>/dev/null; then
    echo "  Installing Node.js..."
    if [ "$PKG" = "apt" ]; then
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
        sudo apt-get install -y nodejs
    elif [ "$PKG" = "dnf" ]; then
        sudo dnf install -y nodejs npm
    elif [ "$PKG" = "brew" ]; then
        brew install node
    fi
else
    echo "  Node.js $(node --version) already installed."
fi
echo ""

# ── Main Python venv ────────────────────────────
echo "[4/5] Setting up main Python environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
deactivate
echo "  Done."
echo ""

# ── Portal backend venv ─────────────────────────
echo "[5/5] Setting up portal backend + building frontend..."
if [ ! -d "portal/backend/venv" ]; then
    python3 -m venv portal/backend/venv
fi
source portal/backend/venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r portal/backend/requirements.txt
deactivate

# ── Frontend build ──────────────────────────────
cd portal/frontend
npm install --silent
npm run build
cd ../..
echo "  Done."
echo ""

echo "============================================"
echo " Setup complete!"
echo ""
echo " To start:   bash start-portal.sh"
echo " To update:  git pull && bash install.sh"
echo "============================================"
