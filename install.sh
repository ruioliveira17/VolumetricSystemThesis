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

mkdir -p "$PROJECT_DIR/backend/data"

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
    --default-background-color=0a0a0a \
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

# Configure Qubic discovery systemd service
sudo tee /etc/systemd/system/qubic-discovery.service > /dev/null <<EOF
[Unit]
Description=Qubic Network Discovery
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$(id -un)
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/.venv/bin/python $PROJECT_DIR/discovery.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now qubic
sudo systemctl enable --now qubic-discovery

# Configure LXDE autostart
mkdir -p "$HOME/.config/lxsession/rpd-x"

cat > "$HOME/.config/lxsession/rpd-x/autostart" <<EOF
@$HOME/start_qubic.sh
EOF

# Disable the internal WiFi chip (the metal enclosure blocks the signal).
# External USB WiFi adapters keep working.
BOOT_CONFIG="/boot/firmware/config.txt"

if ! grep -q "^dtoverlay=disable-wifi" "$BOOT_CONFIG"; then
    echo "dtoverlay=disable-wifi" | sudo tee -a "$BOOT_CONFIG" > /dev/null
    echo "Internal WiFi disabled (takes effect after reboot)."
else
    echo "Internal WiFi already disabled."
fi

# Network failover: wired (eth0) preferred while it has internet,
# otherwise fall back to WiFi (the wired link can stay up through the
# internal switch even with no uplink, so NetworkManager can't detect it).

# Default route metrics for any WiFi profile (wired uses 100 in the script)
sudo tee /etc/NetworkManager/conf.d/30-metrics.conf > /dev/null <<'NM_EOF'
[connection-wifi]
match-device=type:wifi
ipv4.route-metric=200
NM_EOF

sudo tee /usr/local/bin/netfailover.sh > /dev/null <<'NETFAILOVER_EOF'
#!/bin/bash
# Cabo (eth0) preferido quando tem internet; WiFi quando o cabo falha.

IFACE=eth0
TEST_URL=http://1.1.1.1
GOOD=100     # cabo com internet (preferido)
BAD=700      # cabo sem internet (WiFi, com 200, passa a ganhar)

while true; do
  GW=$(nmcli -g IP4.GATEWAY device show "$IFACE" 2>/dev/null)

  if [ -n "$GW" ]; then
    if curl -s --interface "$IFACE" --connect-timeout 1 --max-time 2 -o /dev/null "$TEST_URL"; then
      WANT=$GOOD
    else
      WANT=$BAD
    fi

    CURRENT=$(ip route show default dev "$IFACE" | grep -o 'metric [0-9]*' | head -n1 | cut -d' ' -f2)

    if [ "$CURRENT" != "$WANT" ]; then
      ip route del default dev "$IFACE" 2>/dev/null
      ip route add default via "$GW" dev "$IFACE" metric "$WANT"
      echo "$(date +%T) $IFACE metric -> $WANT"
    fi
  fi

  sleep 1
done
NETFAILOVER_EOF

sudo chmod +x /usr/local/bin/netfailover.sh

sudo tee /etc/systemd/system/netfailover.service > /dev/null <<'SERVICE_EOF'
[Unit]
Description=Qubic network failover (eth0 -> WiFi)
After=NetworkManager.service
Wants=NetworkManager.service

[Service]
Type=simple
ExecStart=/usr/local/bin/netfailover.sh
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
SERVICE_EOF

sudo systemctl daemon-reload
sudo systemctl enable --now netfailover

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