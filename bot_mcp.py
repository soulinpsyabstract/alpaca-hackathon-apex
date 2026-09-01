"""
bot_mcp.py — MCP server exposing Alpaca trading tools to Claude.
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

ALPACA_API_KEY = os.environ.get("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.environ.get("ALPACA_SECRET_KEY", "")
ALPACA_BASE_URL = os.environ.get("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
SIGNAL_FILE = Path(__file__).parent / "signal.json"


from alpaca_trade_api import REST  # noqa: E402
from alpaca.trading.client import TradingClient  # noqa: E402
from alpaca.trading.requests import GetOptionContractsRequest, MarketOrderRequest  # noqa: E402
from alpaca.trading.enums import ContractType, OrderSide, TimeInForce  # noqa: E402

def get_api():
    """Lazy load API only when needed"""
    return REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL)

# Options trading is required by the hackathon rules across all 4 tracks, and
# alpaca_trade_api (legacy REST above) has no options support at all -- no
# get_option_contracts, no options order path. alpaca-py (TradingClient) is
# Alpaca's current SDK and does support it, so it's used for options only,
# alongside the legacy client for everything equities-related.
trading_client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=True)

app = FastAPI(title="alpaca-mcp-bot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/tools/get_account")
def get_account():
    try:
        account = get_api().get_account()
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
        positions = get_api().list_positions()
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
        bars = get_api().get_bars(symbol, timeframe, limit=limit)
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
def place_order(symbol: str, qty: float, side: str, stop_price: float = None):
    """
    Places a market order — matches strategy_prompt.md: "Market orders (no limit
    order games)". side must be "buy" or "sell".

    stop_price (optional): if provided, attaches a real stop-loss to the order
    via Alpaca's OTO (one-triggers-other) order class, matching strategy_prompt.md's
    "Stop loss: VWAP ± 1 ATR" rule. Pass the actual stop price you calculated
    (e.g. VWAP - 1*ATR for a long, VWAP + 1*ATR for a short).

    Uses order_class="oto", not "bracket" -- bracket orders require BOTH a
    take_profit and a stop_loss leg per Alpaca's API spec. We only ever set a
    stop_loss here, so oto (entry + one child order) is the correct class.

    Example: POST /tools/place_order?symbol=SPY&qty=1&side=buy&stop_price=418.50
    """
    side = side.lower()
    if side not in ("buy", "sell"):
        raise HTTPException(status_code=400, detail="side must be 'buy' or 'sell'")

    if qty <= 0:
        raise HTTPException(status_code=400, detail="qty must be greater than 0")

    order_kwargs = {
        "symbol": symbol,
        "qty": qty,
        "side": side,
        "type": "market",
        "time_in_force": "day",
    }

    if stop_price is not None:
        if stop_price <= 0:
            raise HTTPException(status_code=400, detail="stop_price must be greater than 0")
        order_kwargs["order_class"] = "oto"
        order_kwargs["stop_loss"] = {"stop_price": stop_price}

    try:
        order = get_api().submit_order(**order_kwargs)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Alpaca error: {exc}") from exc

    return {
        "order_id": order.id,
        "symbol": order.symbol,
        "qty": float(order.qty),
        "side": order.side,
        "type": order.type,
        "status": order.status,
        "stop_price": stop_price,
    }


@app.get("/tools/get_option_contracts")
def get_option_contracts(
    underlying_symbol: str,
    option_type: str = None,
    expiration_date: str = None,
    strike_price_gte: float = None,
    strike_price_lte: float = None,
    limit: int = 50,
):
    """
    Looks up tradable option contracts for an underlying symbol -- the OCC
    symbol this returns (e.g. "AAPL240119C00100000") is what place_option_order
    needs. option_type must be "call" or "put" if given. expiration_date is
    "YYYY-MM-DD".

    Example: /tools/get_option_contracts?underlying_symbol=SPY&option_type=call&strike_price_gte=550
    """
    contract_type = None
    if option_type is not None:
        option_type = option_type.lower()
        if option_type not in ("call", "put"):
            raise HTTPException(status_code=400, detail="option_type must be 'call' or 'put'")
        contract_type = ContractType.CALL if option_type == "call" else ContractType.PUT

    try:
        request = GetOptionContractsRequest(
            underlying_symbols=[underlying_symbol],
            type=contract_type,
            expiration_date=expiration_date,
            strike_price_gte=str(strike_price_gte) if strike_price_gte is not None else None,
            strike_price_lte=str(strike_price_lte) if strike_price_lte is not None else None,
            limit=limit,
        )
        response = trading_client.get_option_contracts(request)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Alpaca error: {exc}") from exc

    return {
        "contracts": [
            {
                "symbol": c.symbol,
                "type": c.type.value if c.type else None,
                "strike_price": float(c.strike_price) if c.strike_price is not None else None,
                "expiration_date": str(c.expiration_date),
                "tradable": c.tradable,
                "open_interest": c.open_interest,
            }
            for c in response.option_contracts
        ]
    }


@app.post("/tools/place_option_order")
def place_option_order(symbol: str, qty: int, side: str):
    """
    Places a market order for an option contract by its OCC symbol (from
    get_option_contracts). qty is number of contracts (integer, no fractional
    contracts). side must be "buy" or "sell".

    Example: POST /tools/place_option_order?symbol=AAPL240119C00100000&qty=1&side=buy
    """
    side = side.lower()
    if side not in ("buy", "sell"):
        raise HTTPException(status_code=400, detail="side must be 'buy' or 'sell'")

    if qty <= 0:
        raise HTTPException(status_code=400, detail="qty must be greater than 0")

    order_request = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
        time_in_force=TimeInForce.DAY,
    )

    try:
        order = trading_client.submit_order(order_data=order_request)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Alpaca error: {exc}") from exc

    return {
        "order_id": str(order.id),
        "symbol": order.symbol,
        "qty": float(order.qty),
        "side": order.side.value if hasattr(order.side, "value") else order.side,
        "type": order.type.value if hasattr(order.type, "value") else order.type,
        "status": order.status.value if hasattr(order.status, "value") else order.status,
    }


@app.post("/tools/cancel_order")
def cancel_order(order_id: str):
    """
    Cancels an open order by its ID.
    Example: POST /tools/cancel_order?order_id=abc123
    """
    try:
        get_api().cancel_order(order_id)
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
