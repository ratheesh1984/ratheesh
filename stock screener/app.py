"""
Stock Screener — Streamlit UI

Run:
    streamlit run app.py

Default URL: http://localhost:8501
"""
import logging
from datetime import datetime

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from screener.screener import run_screen
from screener.universe import (
    INDIA_UNIVERSES,
    US_UNIVERSES,
    get_universe,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ──────────────────────────────────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Stock Screener — P/E + Volume + RSI",
    page_icon="📈",
    layout="wide",
)


# ──────────────────────────────────────────────────────────────────────────
# Cached screen runner
# ──────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=55, show_spinner=False)
def cached_run_screen(universe_name: str, tickers_tuple: tuple[str, ...]) -> list[dict]:
    """
    Cache the screening result for ~55s so the 60s autorefresh hits a fresh
    fetch on each cycle but rapid re-renders within the cycle reuse data.
    """
    results = run_screen(list(tickers_tuple))
    return [r.to_dict() for r in results]


# ──────────────────────────────────────────────────────────────────────────
# Sidebar — controls
# ──────────────────────────────────────────────────────────────────────────
st.sidebar.title("⚙️  Controls")

market = st.sidebar.radio(
    "Market",
    ["🇮🇳 India (NSE)", "🇺🇸 USA (NYSE/NASDAQ)"],
    index=0,
)

universes = INDIA_UNIVERSES if market.startswith("🇮🇳") else US_UNIVERSES
universe_name = st.sidebar.selectbox("Universe", universes, index=0)
tickers = get_universe(universe_name)
st.sidebar.caption(f"Scanning **{len(tickers)}** tickers")

st.sidebar.markdown("---")
st.sidebar.markdown("**Filter thresholds**")
st.sidebar.markdown(
    "- P/E: `0 < pe < 20`\n"
    "- Volume ratio: `> 2.0×` 20-day avg\n"
    "- RSI(14): `> 50`"
)

st.sidebar.markdown("---")
auto_refresh = st.sidebar.checkbox("Auto-refresh every 60s", value=True)

if auto_refresh:
    # Triggers a Streamlit rerun every 60 seconds.
    st_autorefresh(interval=3_600_000, key="autorefresh")

manual = st.sidebar.button("🔄  Refresh now")
if manual:
    cached_run_screen.clear()

st.sidebar.markdown("---")
st.sidebar.caption(
    "**Note:** yfinance scrapes Yahoo Finance. Outside market hours, "
    "'current' price is yesterday's close. Volume ratio uses today's "
    "(or last) bar vs. the previous 20 days' average."
)


# ──────────────────────────────────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────────────────────────────────
st.title("📈 Stock Screener")
st.caption(
    f"**{universe_name}** · P/E < 20 · Volume > 2× avg · RSI(14) > 50 · "
    f"ranked by composite score"
)

# ──────────────────────────────────────────────────────────────────────────
# Run screen
# ──────────────────────────────────────────────────────────────────────────
status_box = st.empty()

with st.spinner(f"Screening {len(tickers)} {universe_name} tickers…"):
    try:
        results = cached_run_screen(universe_name, tuple(tickers))
    except Exception as e:
        st.error(f"Screen failed: {e}")
        results = []

last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ──────────────────────────────────────────────────────────────────────────
# Top metrics
# ──────────────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Universe size", len(tickers))
col2.metric("Matches found", len(results))
col3.metric(
    "Top score",
    f"{results[0]['score']:.2f}" if results else "—",
)
col4.metric("Last updated", last_update.split(" ")[1])

# ──────────────────────────────────────────────────────────────────────────
# Results table
# ──────────────────────────────────────────────────────────────────────────
st.markdown("### Ranked Results")

if not results:
    st.info(
        "No tickers match the filter right now. Markets may be closed, "
        "or no stocks in this universe have a current volume spike with "
        "bullish RSI and reasonable P/E. Try a larger universe or wait "
        "for the next refresh."
    )
else:
    df = pd.DataFrame(results)
    df.insert(0, "Rank", range(1, len(df) + 1))
    df = df.rename(columns={
        "ticker": "Ticker",
        "price": "Price",
        "pe": "P/E",
        "volume_ratio": "Vol Ratio",
        "rsi": "RSI(14)",
        "avg_volume": "Avg Vol (20d)",
        "score": "Score",
    })

    # Format columns
    df["Price"] = df["Price"].map(lambda x: f"{x:,.2f}")
    df["P/E"] = df["P/E"].map(lambda x: f"{x:.2f}")
    df["Vol Ratio"] = df["Vol Ratio"].map(lambda x: f"{x:.2f}×")
    df["RSI(14)"] = df["RSI(14)"].map(lambda x: f"{x:.1f}")
    df["Avg Vol (20d)"] = df["Avg Vol (20d)"].map(lambda x: f"{x:,.0f}")
    df["Score"] = df["Score"].map(lambda x: f"{x:.2f}")

    st.dataframe(
        df,
        hide_index=True,
        width="stretch",
        height=min(600, 50 + 35 * len(df)),
    )

    # Download
    csv = pd.DataFrame(results).to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️  Download results as CSV",
        csv,
        f"screener_{universe_name.replace(' ', '_')}_{last_update.replace(':','-').replace(' ','_')}.csv",
        "text/csv",
    )

# ──────────────────────────────────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("ℹ️  How the score works"):
    st.markdown(
        "**Composite score** = `Vol Ratio × (RSI / 50) × (20 / P/E)`\n\n"
        "All three factors equal 1.0 at the filter thresholds, so the score "
        "grows multiplicatively as each metric exceeds its threshold:\n"
        "- A stock with 3× volume, RSI 65, P/E 10 → `3 × 1.3 × 2 = 7.8`\n"
        "- A stock with 2.1× volume, RSI 51, P/E 19 → `2.1 × 1.02 × 1.05 = 2.25`\n\n"
        "Higher score = stronger combined signal across all three filters."
    )

with st.expander("⚠️  Limitations"):
    st.markdown(
        "- **Data source:** yfinance scrapes Yahoo Finance. No official API, "
        "no SLA. Yahoo can throttle or break the scraper.\n"
        "- **Market hours:** Indian NSE 9:15–15:30 IST · US 9:30–16:00 ET. "
        "Outside hours, indicators reflect the last completed session.\n"
        "- **Not financial advice:** This is a screening tool. Do your own "
        "due diligence before any trade."
    )
