# Stock Screener — P/E + Volume + RSI

Near real-time stock screener for Indian NSE and US markets. Filters by:
- **P/E** between 0 and 20 (excludes loss-making companies)
- **Volume** > 2× the 20-day average
- **RSI(14)** > 50

Ranked by a composite score and refreshed every 60 seconds.

## Quick start

```bash
# 1. Clone / cd into the project folder
cd stock-screener

# 2. (Recommended) create a virtual environment
python -m venv .venv
source .venv/bin/activate          # macOS/Linux
# .venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
streamlit run app.py
```

The app opens at **http://localhost:8501**.

## Configuration

- **Port:** `8501` (default Streamlit). Change in `.streamlit/config.toml` or run with `streamlit run app.py --server.port 9000`.
- **Refresh cadence:** 60 seconds (toggleable in the sidebar). Manual refresh is also available.

## Universes available

| Market | Universes | Tickers |
|---|---|---|
| 🇮🇳 India (NSE) | Nifty 50 | 50 |
| | Nifty 100 | ~100 |
| 🇺🇸 USA | Dow 30 | 30 |
| | S&P 500 (Top 100) | 100 |

> **Why no full Nifty 500 / S&P 500 with 1-min refresh?** yfinance scrapes Yahoo Finance, which throttles aggressive callers (~2000 req/hour). Scanning 500 tickers every 60s plus per-ticker P/E lookups would burn through that budget fast and trigger 429s. The screener is designed so you can extend `screener/universe.py` with bigger lists if you accept a longer refresh interval (e.g. 5 min for Nifty 500).

## Rate-limiting strategy

- Batched OHLCV via `yf.download(...)` — one HTTP call covers the whole universe.
- 20-day average volume is computed from the same batch (no extra calls).
- P/E (`Ticker.info`) is fetched **only for tickers that already pass the volume + RSI filter** — typically <20 names per cycle.
- Concurrent P/E fetches capped at 5 workers, with 0.1s pacing between calls.
- Exponential backoff (2s, 4s, 8s) on 429/transient failures.
- Streamlit `@st.cache_data(ttl=55)` prevents duplicate fetches on rapid reruns.

## Project layout

```
stock-screener/
├── CLAUDE.md              # design/architecture notes
├── README.md              # this file
├── requirements.txt
├── app.py                 # Streamlit UI entry point
├── screener/
│   ├── universe.py        # Nifty 50/100, Dow 30, S&P 500 ticker lists
│   ├── indicators.py      # RSI(14), volume ratio
│   ├── fetcher.py         # yfinance batched + retry
│   └── screener.py        # pipeline orchestration
└── .streamlit/
    └── config.toml        # port + theme
```

## Disclaimer

Not investment advice. yfinance is an unofficial scraper of Yahoo Finance — data quality, completeness, and availability are not guaranteed. Verify any signal independently before trading.
