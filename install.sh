#!/bin/bash

set -e

PROJECT_DIR="$HOME/Qubic"
REPO_URL="https://github.com/ruioliveira17/VolumetricSystemThesis.git"

echo "======================================"
echo "        Qubic - Installation"
echo "======================================"

echo "[1/7] Installing system dependencies..."

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

echo "[2/7] Checking project directory..."

if [ -d "$PROJECT_DIR" ]; then
    echo "Project already exists at:"
    echo "$PROJECT_DIR"
    echo "Skipping repository download."
else
    echo "Cloning Qubic..."
    git clone "$REPO_URL" "$PROJECT_DIR"
fi

echo "[3/7] Creating environment files..."

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

echo "[4/7] Creating Python virtual environment..."

if [ ! -d "$PROJECT_DIR/.venv" ]; then
    python3 -m venv "$PROJECT_DIR/.venv"
fi

echo "[5/7] Installing Python dependencies..."

"$PROJECT_DIR/.venv/bin/python" -m pip install --upgrade pip

"$PROJECT_DIR/.venv/bin/pip" install \
    -r "$PROJECT_DIR/requirements.txt"

echo "[6/7] Installing frontend dependencies..."

cd "$PROJECT_DIR/frontend"

npm ci

echo "[7/7] Preparing application data..."

mkdir -p "$PROJECT_DIR/Python/data"

echo ""
echo "======================================"
echo "       Qubic installation done!"
echo "======================================"
echo ""
echo "Project: $PROJECT_DIR"