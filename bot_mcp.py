"""
bot_mcp.py — MCP server exposing Alpaca trading tools to Claude.
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

load_dotenv()

ALPACA_API_KEY = os.environ.get("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.environ.get("ALPACA_SECRET_KEY", "")
ALPACA_BASE_URL = os.environ.get("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
SIGNAL_FILE = Path(__file__).parent / "signal.json"

if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
    print("[bot_mcp] ALPACA_API_KEY / ALPACA_SECRET_KEY missing — fill in .env (see .env.example)")
    sys.exit(1)

from alpaca_trade_api import REST  # noqa: E402

api = REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL)

app = FastAPI(title="alpaca-mcp-bot")


@app.get("/tools/get_account")
def get_account():
    try:
        account = api.get_account()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Alpaca error: {exc}") from exc

    return {
        "cash": float(account.cash),
        "buying_power": float(account.buying_power),
        "portfolio_value": float(account.portfolio_value),
        "equity": float(account.equity),
        "status": account.status,
    }


@app.get("/tools/get_positions")
def get_positions():
    try:
        positions = api.list_positions()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Alpaca error: {exc}") from exc

    return {
        "positions": [
            {
                "symbol": p.symbol,
                "qty": float(p.qty),
                "side": p.side,
                "avg_entry_price": float(p.avg_entry_price),
                "current_price": float(p.current_price),
                "unrealized_pl": float(p.unrealized_pl),
                "market_value": float(p.market_value),
            }
            for p in positions
        ]
    }


@app.get("/tools/get_bars")
def get_bars(symbol: str, timeframe: str = "15Min", limit: int = 50):
    """
    Returns OHLCV bars for a symbol. Example:
      /tools/get_bars?symbol=SPY&timeframe=15Min&limit=20
    Valid timeframes: 1Min, 5Min, 15Min, 1Hour, 1Day
    """
    try:
        bars = api.get_bars(symbol, timeframe, limit=limit)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Alpaca error: {exc}") from exc

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "bars": [
            {
                "t": str(bar.t),
                "open": float(bar.o),
                "high": float(bar.h),
                "low": float(bar.l),
                "close": float(bar.c),
                "volume": int(bar.v),
            }
            for bar in bars
        ],
    }


@app.post("/tools/place_order")
def place_order(symbol: str, qty: float, side: str):
    """
    Places a market order — matches strategy_prompt.md: "Market orders (no limit
    order games)". side must be "buy" or "sell".
    Example: POST /tools/place_order?symbol=SPY&qty=1&side=buy
    """
    side = side.lower()
    if side not in ("buy", "sell"):
        raise HTTPException(status_code=400, detail="side must be 'buy' or 'sell'")

    try:
        order = api.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type="market",
            time_in_force="day",
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Alpaca error: {exc}") from exc

    return {
        "order_id": order.id,
        "symbol": order.symbol,
        "qty": float(order.qty),
        "side": order.side,
        "type": order.type,
        "status": order.status,
    }


@app.post("/tools/cancel_order")
def cancel_order(order_id: str):
    """
    Cancels an open order by its ID.
    Example: POST /tools/cancel_order?order_id=abc123
    """
    try:
        api.cancel_order(order_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Alpaca error: {exc}") from exc

    return {"order_id": order_id, "status": "cancel_requested"}


@app.get("/tools/get_signal")
def get_signal():
    """
    Reads the current signal written by the strategy logic (Gephel/IFVG detector)
    to signal.json. monitor.py reads this same file for the live dashboard.
    """
    if not SIGNAL_FILE.exists():
        return {"signal": "NONE", "ts": None}
    try:
        data = json.loads(SIGNAL_FILE.read_text())
        return {"signal": data.get("signal", "NONE"), "ts": data.get("ts")}
    except (json.JSONDecodeError, OSError) as exc:
        raise HTTPException(status_code=500, detail=f"Bad signal.json: {exc}") from exc


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, ws="none")
