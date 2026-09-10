#!/bin/bash

set -e

PROJECT_DIR="$HOME/Qubic"
REPO_URL="https://github.com/ruioliveira17/VolumetricSystemThesis.git"

echo "======================================"
echo "        Qubic - Installation"
echo "======================================"

echo "[1/6] Installing system dependencies..."

sudo apt update

sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    nodejs \
    npm

echo "[2/6] Checking project directory..."

if [ -d "$PROJECT_DIR" ]; then
    echo "Project already exists at:"
    echo "$PROJECT_DIR"
    echo "Skipping repository download."
else
    echo "Cloning Qubic..."
    git clone "$REPO_URL" "$PROJECT_DIR"
fi

echo "[3/6] Creating Python virtual environment..."

if [ ! -d "$PROJECT_DIR/.venv" ]; then
    python3 -m venv "$PROJECT_DIR/.venv"
fi

echo "[4/6] Installing Python dependencies..."

"$PROJECT_DIR/.venv/bin/python" -m pip install --upgrade pip

"$PROJECT_DIR/.venv/bin/pip" install \
    -r "$PROJECT_DIR/requirements.txt"

echo "[5/6] Installing frontend dependencies..."

cd "$PROJECT_DIR/frontend"

npm ci

echo "[6/6] Preparing application data..."

mkdir -p "$PROJECT_DIR/Python/data"

echo ""
echo "======================================"
echo "       Qubic installation done!"
echo "======================================"
echo ""
echo "Project: $PROJECT_DIR"