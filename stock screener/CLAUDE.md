# Stock Screener — Project Guide

## Purpose
Near real-time stock screener for **Indian NSE (Nifty)** and **US NYSE/Dow/S&P** stocks using yfinance. Filters by:
- **P/E ratio** in range `(0, 20)` — excludes loss-making companies
- **Volume spike** — current day volume > 2× the 20-day average
- **RSI(14)** > 50 — bullish momentum

## Stack
- **Language:** Python 3.10+
- **Data:** `yfinance` (Yahoo Finance scraper — no official API, no key required)
- **UI:** Streamlit (auto-refresh every 60s)
- **Default port:** `8501`

## Architecture

```
stock-screener/
├── CLAUDE.md              # this file
├── README.md              # user-facing run instructions
├── requirements.txt
├── app.py                 # Streamlit UI (entry point)
├── screener/
│   ├── __init__.py
│   ├── universe.py        # ticker lists (Nifty 50/100/500, Dow 30, S&P 500)
│   ├── indicators.py      # RSI calculation
│   ├── fetcher.py         # batched yfinance downloads with rate limiting
│   └── screener.py        # orchestrates fetch + filter + rank
└── .streamlit/
    └── config.toml        # port + theme
```

## Rate-Limiting Strategy
yfinance scrapes Yahoo Finance, which throttles ~2000 req/hour per IP. To stay under:
1. **Batch price/volume** via `yf.download(tickers, period="30d")` — one HTTP call for many tickers.
2. **Cache 20-day average volume** for the trading day (it does not change intraday). Recompute once per day or on universe change. Streamlit `@st.cache_data(ttl=...)` handles this.
3. **P/E lookup is per-ticker** (`Ticker.info` is one call each). Only fetch P/E for stocks that **pass the volume + RSI filter** — typically <20 names. This keeps per-cycle calls low.
4. **Sleep 0.1s between info calls** to be polite.
5. **Exponential backoff on 429**: `time.sleep(2**n)` up to 3 retries.
6. **Concurrent fetch via `ThreadPoolExecutor`** with `max_workers=5` for P/E lookups.

## Refresh Cadence
- Streamlit `st_autorefresh` triggers UI rerun every **60 seconds**.
- Cached layers (TTLs):
  - Ticker universe: 24h
  - 20-day volume average: 6h (refreshes at market open)
  - Price/volume bar data: 60s (drives the actual refresh)
  - Per-ticker P/E `info`: 5min

## Filter Pipeline
1. Pull last 30 trading days of OHLCV for the chosen universe (one batched call).
2. Compute for each ticker:
   - `current_price` = last close
   - `volume_ratio` = today_volume / mean(last 20 days excluding today)
   - `rsi_14` = Wilder's RSI on closes
3. Apply: `volume_ratio > 2.0` AND `rsi_14 > 50`.
4. For survivors only, fetch `trailingPE`. Apply `0 < pe < 20`.
5. Compute `composite_score = volume_ratio × (rsi/50) × (20/pe)`.
6. Sort by composite descending. Display top results.

## UI Columns
| Ticker | Price | P/E | Vol Ratio | RSI(14) | Score |

Sortable. Color: green for vol_ratio > 3 or RSI > 70.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```
Opens on http://localhost:8501

## Known Limitations
- **No official API** — Yahoo can change HTML/JSON structure and break yfinance.
- **Indian market hours:** 9:15–15:30 IST. Outside hours, "current" volume is yesterday's close.
- **US market hours:** 9:30–16:00 ET. Same caveat.
- **Penny stocks / illiquid names** can produce nonsensical volume ratios on low base — we filter `avg_volume > 50000`.
- yfinance occasionally returns NaN for individual tickers in batched downloads; we skip and log.

## Not in Scope (v1)
- Order placement / brokerage integration
- Historical backtesting
- Email/Slack alerts
- Persistent storage of past screener runs
