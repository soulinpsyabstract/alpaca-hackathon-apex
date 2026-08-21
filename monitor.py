"""
monitor.py — standalone live monitor for the Alpaca paper trading account.

Prints one line per poll:
  [TIME] Signal: {signal} | Position: {position} | PnL: {pnl}

Signal comes from signal.json (optional, written by bot_mcp.py once that
exists) — {"signal": "BULLISH IFVG", "ts": "..."}. Until bot_mcp.py writes
one, this shows "NONE" and monitor.py still works standalone against Alpaca.

Usage:
  source venv/bin/activate
  python monitor.py
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ALPACA_API_KEY = os.environ.get("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.environ.get("ALPACA_SECRET_KEY", "")
ALPACA_BASE_URL = os.environ.get("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
INTERVAL = int(os.environ.get("MONITOR_INTERVAL", "30"))
SIGNAL_FILE = Path(__file__).parent / "signal.json"

if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
    print("[monitor] ALPACA_API_KEY / ALPACA_SECRET_KEY missing — fill in .env (see .env.example)")
    sys.exit(1)

from alpaca_trade_api import REST  # noqa: E402

api = REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL)


def read_signal() -> str:
    if not SIGNAL_FILE.exists():
        return "NONE"
    try:
        data = json.loads(SIGNAL_FILE.read_text())
        return data.get("signal", "NONE")
    except (json.JSONDecodeError, OSError):
        return "NONE"


def format_position(positions) -> str:
    if not positions:
        return "None"
    parts = [f"{p.side.upper()} {p.qty} {p.symbol}" for p in positions]
    return ", ".join(parts)


def format_pnl(account, positions) -> str:
    unrealized = sum(float(p.unrealized_pl) for p in positions)
    equity = float(account.equity)
    last_equity = float(account.last_equity)
    day_pnl = equity - last_equity
    sign = "+" if day_pnl >= 0 else ""
    return f"{sign}${day_pnl:.2f} (day) / unrealized ${unrealized:.2f}"


def poll_once() -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    try:
        account = api.get_account()
        positions = api.list_positions()
    except Exception as exc:  # noqa: BLE001 — surface any Alpaca/network error, keep polling
        print(f"[{ts}] ERROR fetching Alpaca state: {exc}")
        return

    signal = read_signal()
    position = format_position(positions)
    pnl = format_pnl(account, positions)
    print(f"[{ts}] Signal: {signal} | Position: {position} | PnL: {pnl}")


def main() -> None:
    print(f"[monitor] polling every {INTERVAL}s · base_url={ALPACA_BASE_URL}")
    try:
        account = api.get_account()
        print(f"[monitor] connected · account balance: ${float(account.portfolio_value):.2f}")
    except Exception as exc:  # noqa: BLE001
        print(f"[monitor] FAILED to connect to Alpaca: {exc}")
        sys.exit(1)

    while True:
        poll_once()
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
