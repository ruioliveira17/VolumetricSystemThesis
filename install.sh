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

# Generate a random JWT secret
JWT_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')

# Backend .env
cat > "$PROJECT_DIR/.env" <<EOF
JWT_SECRET_KEY=$JWT_SECRET_KEY
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ADMIN_REGISTER_CODE=ADMBM
EOF

# Get Raspberry Pi local IP
RASPBERRY_IP=$(hostname -I | awk '{print $1}')

# Frontend .env
cat > "$PROJECT_DIR/frontend/.env" <<EOF
VITE_API_URL=http://$RASPBERRY_IP:8000
EOF

echo "Backend .env created."
echo "Frontend .env created with API URL: http://$RASPBERRY_IP:8000"

echo "[4/8] Creating Python virtual environment..."

if [ ! -d "$PROJECT_DIR/.venv" ]; then
    python3 -m venv "$PROJECT_DIR/.venv"
fi

echo "[5/8] Installing Python dependencies..."

"$PROJECT_DIR/.venv/bin/python" -m pip install --upgrade pip

"$PROJECT_DIR/.venv/bin/pip" install \
    -r "$PROJECT_DIR/requirements.txt"

echo "[6/8] Installing frontend dependencies..."

cd "$PROJECT_DIR/frontend"

npm ci

echo "[7/8] Preparing application data..."

mkdir -p "$PROJECT_DIR/Python/data"

echo "[8/8] Configuring automatic startup..."

# Install Chromium
sudo apt install -y chromium

# Create Qubic startup script
cat > "$HOME/start_qubic.sh" <<EOF
#!/bin/bash

sleep 3
/usr/bin/chromium --kiosk --password-store=basic http://localhost:5173
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