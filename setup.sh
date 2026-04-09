#!/bin/bash
# Setup script for Market Analyzer on Raspberry Pi 5
# Usage: bash setup.sh

set -e

echo "╔════════════════════════════════════════╗"
echo "║  Market Analyzer Setup Script          ║"
echo "║  Raspberry Pi 5 Edition                ║"
echo "╚════════════════════════════════════════╝"

# Check Python version
echo "[1/5] Checking Python version..."
python3 --version

# Create virtual environment
echo "[2/5] Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "[3/5] Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "[4/5] Upgrading pip and setuptools..."
pip install --upgrade pip setuptools wheel

# Install requirements
echo "[5/5] Installing requirements..."
pip install -r requirements.txt

echo ""
echo "╔════════════════════════════════════════╗"
echo "║  Setup Complete!                      ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "1. Configure settings in config.py"
echo "2. Set Telegram credentials:"
echo "   export TELEGRAM_BOT_TOKEN='your_token'"
echo "   export TELEGRAM_CHAT_ID='your_chat_id'"
echo "3. Run the application:"
echo "   source venv/bin/activate"
echo "   python main.py          # CLI mode"
echo "   python main.py --gui    # GUI mode"
echo ""
echo "For help, see README.md"
