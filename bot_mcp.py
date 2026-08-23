"""
bot_mcp.py — MCP server exposing Alpaca trading tools to Claude.

Day 1 target: get_account() returning real balance / buying power data
from the Alpaca paper trading account.

Usage:
  source venv/bin/activate
  python bot_mcp.py
  # then in another terminal:
  curl http://localhost:8000/tools/get_account
"""

import os
import sys

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

load_dotenv()

ALPACA_API_KEY = os.environ.get("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.environ.get("ALPACA_SECRET_KEY", "")
ALPACA_BASE_URL = os.environ.get("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
    print("[bot_mcp] ALPACA_API_KEY / ALPACA_SECRET_KEY missing — fill in .env (see .env.example)")
    sys.exit(1)

from alpaca_trade_api import REST  # noqa: E402

api = REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL)

app = FastAPI(title="alpaca-mcp-bot")


@app.get("/tools/get_account")
def get_account():
    """
    Returns account balance, buying power, and equity from the
    Alpaca paper trading account. This is the Day 1 deliverable.
    """
    try:
        account = api.get_account()
    except Exception as exc:  # noqa: BLE001 — surface Alpaca/auth/network errors clearly
        raise HTTPException(status_code=502, detail=f"Alpaca error: {exc}") from exc

    return {
        "cash": float(account.cash),
        "buying_power": float(account.buying_power),
        "portfolio_value": float(account.portfolio_value),
        "equity": float(account.equity),
        "status": account.status,
    }


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, ws="none")
