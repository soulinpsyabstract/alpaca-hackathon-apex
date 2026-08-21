#!/usr/bin/env bash
# setup.sh — deployment skeleton for the Alpaca trading bot hackathon
# Run once the team repo exists: git clone <repo> && cd <repo> && bash setup.sh
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d venv ]; then
  python3 -m venv venv
  echo "[setup] venv created"
else
  echo "[setup] venv already exists, skipping"
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo "[setup] .env created from .env.example — fill in ALPACA_API_KEY / ALPACA_SECRET_KEY / ANTHROPIC_API_KEY"
else
  echo "[setup] .env already exists, not overwriting"
fi

echo ""
echo "[setup] DONE. Next:"
echo "  1. Edit .env with real keys"
echo "  2. source venv/bin/activate"
echo "  3. python monitor.py"
