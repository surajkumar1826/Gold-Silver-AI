import pandas as pd
import yfinance as yf
import streamlit as st

TICKERS = {"Gold": "GC=F", "Silver": "SI=F"}

def fetch_new_bars(ticker, last_ts):
    df = yf.download(ticker, period="60d", interval="1h",
                     progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.index = df.index.tz_convert("Asia/Kolkata")
    return df[df.index > last_ts][["Close"]]

@st.cache_data(ttl=300)  # 5 min me ek hi baar download
def load_fresh(csv_path, price_col, asset):
    hist = pd.read_csv(csv_path, parse_dates=[0], index_col=0)
    hist.index = pd.to_datetime(hist.index, utc=True).tz_convert("Asia/Kolkata")
    new = fetch_new_bars(TICKERS[asset], hist.index.max())
    new = new.rename(columns={"Close": price_col})
    full = pd.concat([hist[[price_col]], new])
    return full[~full.index.duplicated(keep="last")].sort_index()
