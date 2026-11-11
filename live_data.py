import pandas as pd
import streamlit as st
import yfinance as yf

TICKERS = {"Gold": "GC=F", "Silver": "SI=F"}


@st.cache_data(ttl=60, show_spinner=False)
def get_live_prices():
    """Returns {'Gold': {'price':..,'time':..}, 'Silver': {...}} or None"""
    out = {}
    for name, ticker in TICKERS.items():
        try:
            df = yf.download(ticker, period="5d", interval="1m",
                             progress=False, auto_adjust=True)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            s = df["Close"].dropna()
            if s.empty:
                return None
            ts = pd.Timestamp(s.index[-1])
            if ts.tzinfo is None:
                ts = ts.tz_localize("UTC")
            out[name] = {"price": float(s.iloc[-1]),
                         "time": ts.tz_convert("Asia/Kolkata")}
        except Exception:
            return None
    return out


def render_banner(csv_gold, csv_silver):
    live = get_live_prices()
    st.subheader("Live Prices")
    if not live:
        st.warning("Live data nahi mila, CSV ka purana price use ho raha hai.")
        return
    c1, c2, c3 = st.columns([2, 2, 1])
    c1.metric("Gold (live)", f"${live['Gold']['price']:,.2f}",
              f"{live['Gold']['price'] - csv_gold:+,.2f} vs CSV")
    c2.metric("Silver (live)", f"${live['Silver']['price']:,.2f}",
              f"{live['Silver']['price'] - csv_silver:+,.2f} vs CSV")
    c3.write("")
    if c3.button("Refresh", key="live_refresh"):
        get_live_prices.clear()
        st.rerun()
    st.caption("Last live bar (IST): " + live["Gold"]["time"].strftime("%Y-%m-%d %H:%M")
               + " | Source: Yahoo Finance futures (GC=F, SI=F), 1 min cache")
