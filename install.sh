#!/bin/bash

set -e

PROJECT_DIR="$HOME/Qubic"
REPO_URL="https://github.com/ruioliveira17/VolumetricSystemThesis.git"

echo "======================================"
echo "        Qubic - Installation"
echo "======================================"

echo "[1/8] Installing system dependencies..."

sudo apt update

sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl

if ! command -v node >/dev/null 2>&1; then
    echo "Node.js not found. Installing Node.js 20..."

    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs
else
    echo "Node.js already installed: $(node --version)"
fi

echo "Node.js: $(node --version)"
echo "npm: $(npm --version)"

echo "[2/8] Checking project directory..."

if [ -d "$PROJECT_DIR" ]; then
    echo "Project already exists at:"
    echo "$PROJECT_DIR"
    echo "Skipping repository download."
else
    echo "Cloning Qubic..."
    git clone "$REPO_URL" "$PROJECT_DIR"
fi

echo "[3/8] Creating environment files..."

# Generate a random JWT secret only if .env does not already exist
if [ ! -f "$PROJECT_DIR/.env" ]; then
    JWT_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')

    cat > "$PROJECT_DIR/.env" <<EOF
JWT_SECRET_KEY=$JWT_SECRET_KEY
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
EOF

    echo "Backend .env created."
else
    echo "Backend .env already exists. Keeping existing configuration."
fi

echo "[4/8] Creating Python virtual environment..."

if [ ! -d "$PROJECT_DIR/.venv" ]; then
    python3 -m venv "$PROJECT_DIR/.venv"
    echo "Python virtual environment created."
else
    echo "Python virtual environment already exists."
fi

echo "[5/8] Installing Python dependencies..."

"$PROJECT_DIR/.venv/bin/python" -m pip install --upgrade pip

"$PROJECT_DIR/.venv/bin/pip" install \
    -r "$PROJECT_DIR/requirements.txt"

echo "[6/8] Installing frontend dependencies..."

cd "$PROJECT_DIR/frontend"

if [ ! -d "$PROJECT_DIR/frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm ci
else
    echo "Frontend dependencies already installed."
fi

echo "Building frontend..."
npm run build

echo "[7/8] Preparing application data..."

SDK_LIB_DIR="$PROJECT_DIR/AArch64/ScepterSDK/Lib"
SDK_DRIVERS_DIR="$SDK_LIB_DIR/Drivers"
SDK_FILE="$SDK_LIB_DIR/libScepter_api.so"

if [ ! -f "$SDK_FILE" ]; then
    echo "ERROR: ScepterSDK library not found:"
    echo "$SDK_FILE"
    exit 1
fi

if [ ! -d "$SDK_DRIVERS_DIR" ]; then
    echo "ERROR: ScepterSDK Drivers directory not found:"
    echo "$SDK_DRIVERS_DIR"
    exit 1
fi

mkdir -p "$PROJECT_DIR/Python/data"

echo "[8/8] Configuring automatic startup..."

# Install Chromium
sudo apt install -y chromium

# Create Qubic startup script
cat > "$HOME/start_qubic.sh" <<EOF
#!/bin/bash

while ! curl -s http://localhost:8000 > /dev/null; do
    sleep 0.2
done

/usr/bin/chromium \
    --kiosk \
    --password-store=basic \
    --force-dark-mode \
    http://localhost:8000 &
EOF

chmod +x "$HOME/start_qubic.sh"

# Configure Qubic systemd service
sudo tee /etc/systemd/system/qubic.service > /dev/null <<EOF
[Unit]
Description=Qubic Application
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$(id -un)
WorkingDirectory=$PROJECT_DIR
Environment="LD_LIBRARY_PATH=$PROJECT_DIR/AArch64/ScepterSDK/Lib:$PROJECT_DIR/AArch64/ScepterSDK/Lib/Drivers"
ExecStart=$PROJECT_DIR/.venv/bin/python $PROJECT_DIR/run_api.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable qubic

# Configure LXDE autostart
mkdir -p "$HOME/.config/lxsession/rpd-x"

cat > "$HOME/.config/lxsession/rpd-x/autostart" <<EOF
@$HOME/start_qubic.sh
EOF

echo "Automatic startup configured."

echo ""
echo "======================================"
echo "       Qubic installation done!"
echo "======================================"
echo ""
echo "Project: $PROJECT_DIR"
echo ""
read -r -p "Do you want to reboot now? [y/n]: " REBOOT < /dev/tty

if [[ "$REBOOT" =~ ^[Yy]$ ]]; then
    echo "Rebooting..."
    sudo reboot
else
    echo "Reboot skipped."
    echo "You can reboot later with: sudo reboot"
fi