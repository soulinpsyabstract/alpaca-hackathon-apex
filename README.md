# Alpaca trading bot — hackathon deployment skeleton

Aelin's Day 1-3 deliverables: deployment skeleton + monitor.py.
`bot_mcp.py` (MCP tools: get_account, get_bars, place_order, get_positions) is Nisha's — not built here.

## Setup

```bash
bash setup.sh
```

This creates `venv/`, installs `requirements.txt`, and copies `.env.example` → `.env`.
Fill in `.env` with real Alpaca paper keys (and `ANTHROPIC_API_KEY` once `bot_mcp.py` exists).

## Run the monitor

```bash
source venv/bin/activate
python monitor.py
```

Prints one line per poll:

```
[14:30:05] Signal: NONE | Position: None | PnL: +$0.00 (day) / unrealized $0.00
```

`Signal` reads from `signal.json` in this directory if present — once `bot_mcp.py` writes
`{"signal": "BULLISH IFVG", "ts": "..."}` there, monitor.py picks it up automatically, no
code change needed on either side.

## Known blockers (2026-08-21)

- `ANTHROPIC_API_KEY` in the shared `.sipa_env` is out of credits — confirmed via direct
  `api.anthropic.com` call, not assumed. Doesn't block `monitor.py` (Alpaca-only), does block
  `bot_mcp.py` once Nisha builds it. Needs a top-up or a different key before Day 1 tool calls work.
- No `ALPACA_API_KEY` / `ALPACA_SECRET_KEY` yet — get a free paper trading key at
  https://app.alpaca.markets/paper/dashboard/overview and put it in `.env`.
