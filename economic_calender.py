import pandas as pd
import requests
import streamlit as st

ICON = {"high": "🔴 High", "medium": "🟠 Medium", "low": "🟢 Low"}


def _get_key():
    try:
        return st.secrets["FINNHUB_KEY"]
    except Exception:
        return None


@st.cache_data(ttl=3600)
def _from_finnhub(key, start, end):
    url = "https://finnhub.io/api/v1/calendar/economic"
    r = requests.get(url, params={"from": start, "to": end, "token": key}, timeout=15)
    r.raise_for_status()
    data = r.json().get("economicCalendar", [])
    df = pd.DataFrame(data)
    if df.empty:
        return df
    df = df.rename(columns={"time": "date", "estimate": "forecast", "prev": "previous"})
    return df[["date", "event", "country", "impact", "forecast", "previous", "actual"]]


def load_events():
    """Returns (DataFrame, source_name)"""
    key = _get_key()
    if key:
        try:
            today = pd.Timestamp.now().normalize()
            df = _from_finnhub(key, str(today.date()),
                               str((today + pd.Timedelta(days=30)).date()))
            if not df.empty:
                return df, "Finnhub API"
        except Exception:
            pass
    try:
        return pd.read_csv("events.csv"), "events.csv (manual)"
    except Exception:
        return pd.DataFrame(), "none"


def get_upcoming(df, n=8):
    if df.empty:
        return df
    d = df.copy()
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    d = d[d["date"] >= pd.Timestamp.now().normalize()].sort_values("date")
    d["date"] = d["date"].dt.strftime("%Y-%m-%d %H:%M")
    return d.head(n)


def render():
    st.subheader("Economic Calendar")
    df, src = load_events()
    st.caption(f"Source: {src}")
    if df.empty:
        st.warning("Koi event data nahi mila. events.csv check karo.")
        return

    df = df.copy()
    df["impact"] = df["impact"].astype(str).str.lower().map(ICON).fillna(df["impact"])
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date")

    f1, f2 = st.columns(2)
    imp = f1.multiselect("Impact", ["🔴 High", "🟠 Medium", "🟢 Low"],
                         default=["🔴 High", "🟠 Medium"], key="ec_imp")
    ctry = f2.multiselect("Country", sorted(df["country"].dropna().unique()),
                          default=["US"] if "US" in df["country"].values else None,
                          key="ec_ctry")
    if imp:
        df = df[df["impact"].isin(imp)]
    if ctry:
        df = df[df["country"].isin(ctry)]

    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption("High impact events (FOMC, CPI, NFP) pe gold/silver me tez volatility aati hai.")
