"""
Ticker universes.

For Indian stocks, yfinance requires the ".NS" suffix (NSE).
For US stocks, plain ticker symbols work.

These lists are static snapshots. For production, fetch from:
  - NSE: https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv
  - S&P 500: https://en.wikipedia.org/wiki/List_of_S%26P_500_companies
"""

# Nifty 50 — top 50 Indian stocks by free-float market cap
# Nifty 50 — top 50 Indian stocks by free-float market cap (May 2026)
NIFTY_50 = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "BHARTIARTL.NS", "ICICIBANK.NS",
    "INFY.NS", "SBIN.NS", "HINDUNILVR.NS", "ITC.NS", "LT.NS",
    "HCLTECH.NS", "BAJFINANCE.NS", "KOTAKBANK.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "M&M.NS", "AXISBANK.NS", "NTPC.NS", "ULTRACEMCO.NS", "TITAN.NS",
    "ONGC.NS", "ADANIENT.NS", "POWERGRID.NS", "WIPRO.NS", "ADANIPORTS.NS",
    "TMPV.NS", "JSWSTEEL.NS", "ASIANPAINT.NS", "COALINDIA.NS", "BAJAJFINSV.NS",
    "NESTLEIND.NS", "BEL.NS", "TATASTEEL.NS", "TRENT.NS", "GRASIM.NS",
    "SBILIFE.NS", "HDFCLIFE.NS", "TECHM.NS", "HINDALCO.NS", "DRREDDY.NS",
    "CIPLA.NS", "EICHERMOT.NS", "BAJAJ-AUTO.NS", "BPCL.NS", "TATACONSUM.NS",
    "BRITANNIA.NS", "APOLLOHOSP.NS", "HEROMOTOCO.NS", "INDUSINDBK.NS", "SHRIRAMFIN.NS",
]

# Nifty Next 50
NIFTY_NEXT_50 = [
    "ADANIGREEN.NS", "ADANIPOWER.NS", "AMBUJACEM.NS", "BAJAJHLDNG.NS", "BANKBARODA.NS",
    "BERGEPAINT.NS", "BOSCHLTD.NS", "CANBK.NS", "CHOLAFIN.NS", "COLPAL.NS",
    "DABUR.NS", "DIVISLAB.NS", "DLF.NS", "DMART.NS", "GAIL.NS",
    "GODREJCP.NS", "HAVELLS.NS", "HAL.NS", "ICICIGI.NS", "ICICIPRULI.NS",
    "INDIGO.NS", "IOC.NS", "IRFC.NS", "JINDALSTEL.NS", "LICI.NS",
    "LODHA.NS", "MARICO.NS", "MOTHERSON.NS", "NAUKRI.NS", "PFC.NS",
    "PIDILITIND.NS", "PNB.NS", "RECLTD.NS", "SBICARD.NS", "SHREECEM.NS",
    "SIEMENS.NS", "SRF.NS", "TATAPOWER.NS", "TORNTPHARM.NS", "TVSMOTOR.NS",
    "UNITDSPR.NS", "VBL.NS", "VEDL.NS", "ETERNAL.NS", "ZYDUSLIFE.NS",
    "ABB.NS", "ATGL.NS", "CGPOWER.NS", "TMCV.NS", "IDBI.NS",
]

NIFTY_100 = NIFTY_50 + NIFTY_NEXT_50

# Dow Jones 30 (current as of 2026)
DOW_30 = [
    "AAPL", "MSFT", "JPM", "V", "WMT",
    "JNJ", "PG", "UNH", "HD", "CVX",
    "MA", "MRK", "AMGN", "MCD", "GS",
    "DIS", "CAT", "AXP", "IBM", "HON",
    "VZ", "BA", "MMM", "NKE", "KO",
    "TRV", "AMZN", "CSCO", "SHW", "CRM",
]

# S&P 500 — top 100 by market cap (curated subset to keep refresh feasible)
SP_500_TOP_100 = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "GOOG", "AMZN", "META", "BRK-B", "LLY", "AVGO",
    "TSLA", "JPM", "WMT", "V", "XOM", "UNH", "MA", "PG", "ORCL", "JNJ",
    "HD", "COST", "ABBV", "BAC", "NFLX", "KO", "CVX", "CRM", "MRK", "AMD",
    "PEP", "TMO", "LIN", "ADBE", "MCD", "ACN", "CSCO", "ABT", "WFC", "PM",
    "DIS", "GE", "DHR", "INTU", "CAT", "VZ", "AMGN", "TXN", "IBM", "QCOM",
    "PFE", "AXP", "ISRG", "GS", "NOW", "MS", "NEE", "RTX", "T", "BLK",
    "UBER", "PGR", "SPGI", "BKNG", "HON", "TJX", "AMAT", "C", "SYK", "BSX",
    "LOW", "PLD", "VRTX", "DE", "ADP", "BX", "GILD", "MDT", "MMC", "BA",
    "CB", "ELV", "ETN", "ADI", "FI", "LRCX", "MU", "REGN", "PANW", "CI",
    "KLAC", "INTC", "CMG", "SO", "SBUX", "ZTS", "BMY", "MO", "DUK", "ICE",
]


UNIVERSE_MAP = {
    # India
    "Nifty 50": NIFTY_50,
    "Nifty 100": NIFTY_100,
    # USA
    "Dow 30": DOW_30,
    "S&P 500 (Top 100)": SP_500_TOP_100,
}

INDIA_UNIVERSES = ["Nifty 50", "Nifty 100"]
US_UNIVERSES = ["Dow 30", "S&P 500 (Top 100)"]


def get_universe(name: str) -> list[str]:
    """Return tickers for the named universe."""
    return UNIVERSE_MAP.get(name, [])
