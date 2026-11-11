import pandas as pd
import streamlit as st
import yfinance as yf
from sklearn.ensemble import RandomForestClassifier

TICKERS = {"Gold": "GC=F", "Silver": "SI=F"}

# (label, interval, period, steps ahead)
HORIZONS = [
    ("1 min",   "1m",  "7d",   1),
    ("5 min",   "5m",  "60d",  1),
    ("15 min",  "15m", "60d",  1),
    ("30 min",  "30m", "60d",  1),
    ("1 hour",  "1h",  "730d", 1),
    ("2 hour",  "1h",  "730d", 2),
    ("4 hour",  "1h",  "730d", 4),
    ("1 day",   "1d",  "10y",  1),
    ("1 week",  "1d",  "10y",  5),
    ("1 month", "1d",  "10y",  21),
]


def _download(ticker, interval, period):
    df = yf.download(ticker, period=period, interval=interval,
                     progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df["Close"].dropna().astype(float)


def _features(close):
    f = pd.DataFrame(index=close.index)
    r = close.pct_change()
    for lag in (1, 2, 3, 5, 10):
        f[f"ret_{lag}"] = close.pct_change(lag)
    for w in (5, 10, 20):
        f[f"sma_{w}"] = close / close.rolling(w).mean() - 1
    for w in (10, 20):
        f[f"vol_{w}"] = r.rolling(w).std()
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    f["rsi"] = 100 - 100 / (1 + gain / (loss + 1e-12))
    return f


def _model():
    return RandomForestClassifier(
        n_estimators=200, max_depth=5, min_samples_leaf=20,
        n_jobs=-1, random_state=42)


@st.cache_data(ttl=600, show_spinner=False)
def predict_one(ticker, interval, period, steps):
    close = _download(ticker, interval, period)
    if len(close) < 300:
        return None

    X = _features(close)
    latest_X = X.dropna().iloc[[-1]]
    future = close.shift(-steps)

    d = X.copy()
    d["y"] = (future > close).astype(int)
    d = d[future.notna()].dropna()
    if len(d) < 250:
        return None

    cols = [c for c in d.columns if c != "y"]
    split = int(len(d) * 0.8)
    train = d.iloc[: split - steps]   # gap: overlap/leakage se bachne ke liye
    test = d.iloc[split:]

    m = _model().fit(train[cols], train["y"])
    acc = float(m.score(test[cols], test["y"]))
    up_share = float(test["y"].mean())
    baseline = max(up_share, 1 - up_share)

    final = _model().fit(d[cols], d["y"])
    classes = list(final.classes_)
    p_up = float(final.predict_proba(latest_X[cols])[0][classes.index(1)]) \
        if 1 in classes else 0.0

    return {
        "direction": "UP" if p_up >= 0.5 else "DOWN",
        "p_up": p_up,
        "acc": acc,
        "baseline": baseline,
        "n": len(d),
        "last_bar": str(close.index[-1]),
        "last_price": float(close.iloc[-1]),
    }


def render():
    st.subheader("Multi-Horizon Direction Predictions")
    st.caption("Har horizon ka alag Random Forest model | live yfinance data | "
               "time-based test split (random nahi)")

    asset = st.selectbox("Asset", list(TICKERS), key="mh_asset")

    if st.button("Predictions chalao", key="mh_run"):
        rows = []
        bar = st.progress(0.0)
        for i, (label, interval, period, steps) in enumerate(HORIZONS):
            try:
                res = predict_one(TICKERS[asset], interval, period, steps)
            except Exception as e:
                res = None
            if res is None:
                rows.append({"Horizon": label, "Direction": "-",
                             "P(UP) %": None, "Test acc %": None,
                             "Baseline %": None, "Verdict": "Data nahi mila"})
            else:
                edge = res["acc"] - res["baseline"]
                verdict = ("Thoda edge" if edge > 0.02
                           else "Koi edge nahi (baseline ke barabar)")
                rows.append({
                    "Horizon": label,
                    "Direction": res["direction"],
                    "P(UP) %": round(res["p_up"] * 100, 1),
                    "Test acc %": round(res["acc"] * 100, 1),
                    "Baseline %": round(res["baseline"] * 100, 1),
                    "Verdict": verdict,
                    "Last bar": res["last_bar"][:16],
                })
            bar.progress((i + 1) / len(HORIZONS))
        bar.empty()
        st.session_state["mh_table"] = pd.DataFrame(rows)

    if "mh_table" in st.session_state:
        st.dataframe(st.session_state["mh_table"],
                     use_container_width=True, hide_index=True)
        st.caption("P(UP) = model ko kitna yakeen hai ki price upar jayega. "
                   "Test acc agar Baseline se zyada nahi, to us horizon ka "
                   "signal bharose layak nahi. Educational use only.")
