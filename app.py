import paper_trading
import economic_calender as economic_calendar
import report
import multi_horizon
import pandas as pd
import joblib
import streamlit as st
# Page settings
st.set_page_config(
    page_title="GoldSilver AI",
    page_icon="📈",
    layout="wide"
)

# Load saved files
@st.cache_data
def load_data():
    return pd.read_csv("gold_silver_dashboard_data.csv")

@st.cache_resource
def load_models():
    from huggingface_hub import hf_hub_download
    path = hf_hub_download(
        repo_id="surajkumar2618/gold-silver-model",
        filename="gold_silver_models.pkl"
    )
    return joblib.load(path)
df = load_data()
models = load_models()

# Website title
st.title("📈 GoldSilver AI Dashboard")
st.subheader(
    "Gold & Silver Correlation, Volatility and ML Analysis"
)

st.info(
    "Educational research dashboard. "
    "Predictions are estimates, not guaranteed trading signals."
)

# Prepare latest observation
features = models["features"]
latest = df.iloc[-1]

X_latest = df[features].iloc[[-1]].astype(float)

# Predictions
gold_price = models["gold_price_model"].predict(X_latest)[0]
silver_price = models["silver_price_model"].predict(X_latest)[0]

gold_direction = models["gold_direction_model"].predict(X_latest)[0]
silver_direction = models["silver_direction_model"].predict(X_latest)[0]

# Latest market information
st.caption(
    "Latest downloaded observation: "
    + str(latest["Timestamp_IST"])
)

# Prediction section
st.header("🤖 Machine Learning Predictions")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Gold")
    st.metric(
        "Latest downloaded price",
        f"${latest['Gold_Close']:,.2f}"
    )
    st.metric(
        "Estimated next-hour price",
        f"${gold_price:,.2f}"
    )
    st.write("Predicted direction:", gold_direction)

with col2:
    st.subheader("Silver")
    st.metric(
        "Latest downloaded price",
        f"${latest['Silver_Close']:,.2f}"
    )
    st.metric(
        "Estimated next-hour price",
        f"${silver_price:,.2f}"
    )
    st.write("Predicted direction:", silver_direction)

# Historical price comparison
st.header("📊 Gold vs Silver Price History")

price_data = df[
    ["Timestamp_IST", "Gold_Close", "Silver_Close"]
].copy()

price_data["Timestamp_IST"] = pd.to_datetime(
    price_data["Timestamp_IST"], errors="coerce"
)

price_data = price_data.set_index("Timestamp_IST")

st.line_chart(
    price_data[["Gold_Close", "Silver_Close"]]
)

# Correlation
st.header("🔗 Gold and Silver Correlation")

correlation = df[
    ["Gold_Return", "Silver_Return"]
].corr().iloc[0, 1]

st.metric(
    "Historical Return Correlation",
    f"{correlation:.4f}"
)

# Volatility
st.header("⚡ Volatility Analysis")

volatility_data = df[
    ["Gold_Volatility", "Silver_Volatility"]
].copy()

st.line_chart(volatility_data)

# Trading session analysis
st.header("🌍 Trading Session Analysis")

sessions = {
    "Asian": "Asian_Session",
    "London": "London_Session",
    "New York": "NewYork_Session",
    "London-New York Overlap": "Overlap_Session"
}

session_results = []

for name, column in sessions.items():

    temp = df[df[column].astype(bool)]

    session_results.append({
        "Session": name,
        "Total Records": len(temp),
        "Gold Volatility": temp["Gold_Return"].std(),
        "Silver Volatility": temp["Silver_Return"].std()
    })

session_table = pd.DataFrame(session_results)

st.dataframe(
    session_table.round(4),
    use_container_width=True
)

# Raw data
with st.expander("View Historical Dataset"):
    st.dataframe(df.tail(100), use_container_width=True)

st.success("GoldSilver AI Dashboard Loaded Successfully!")
# ===== NEW FEATURES =====
prices = {
    "Gold": float(latest["Gold_Close"]),
    "Silver": float(latest["Silver_Close"]),
}
preds = {
    "Gold": {"next": float(gold_price), "direction": str(gold_direction)},
    "Silver": {"next": float(silver_price), "direction": str(silver_direction)},
}
signals = {"Gold": str(gold_direction), "Silver": str(silver_direction)}

st.divider()
tab1, tab2, tab3, tab4 = st.tabs(["Paper Trading", "Economic Calendar", "PDF Report", "Multi-Horizon"])

with tab1:
    paper_trading.render(prices, signals)

with tab2:
    economic_calendar.render()

with tab3:
    st.subheader("PDF Research Report")
    ev, _ = economic_calendar.load_events()
    upcoming = economic_calendar.get_upcoming(ev)
    chart = report.make_chart(
        price_data["Gold_Close"].tail(500),
        price_data["Silver_Close"].tail(500),
    )
    pdf_bytes = report.build_pdf(
        prices, preds, paper_trading.summary(prices), upcoming, chart
    )
    st.download_button(
        "Download PDF report",
        pdf_bytes,
        "goldsilver_report.pdf",
        "application/pdf",
        key="pdf_dl",
    )
with tab4:
    multi_horizon.render()
