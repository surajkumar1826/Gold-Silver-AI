import json
import streamlit as st
import streamlit.components.v1 as components

SYMBOLS = {
    "Gold (XAUUSD)": "OANDA:XAUUSD",
    "Silver (XAGUSD)": "OANDA:XAGUSD",
}

INTERVALS = {
    "1 min": "1", "5 min": "5", "15 min": "15", "30 min": "30",
    "1 hour": "60", "2 hour": "120", "4 hour": "240",
    "1 day": "D", "1 week": "W", "1 month": "M",
}


def render():
    st.subheader("Live TradingView Chart")

    c1, c2 = st.columns(2)
    name = c1.selectbox("Asset", list(SYMBOLS), key="tv_asset")
    tf = c2.selectbox("Timeframe", list(INTERVALS), index=4, key="tv_tf")

    H = 800
    cfg = {
        "autosize": True,
        "symbol": SYMBOLS[name],
        "interval": INTERVALS[tf],
        "timezone": "Asia/Kolkata",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "backgroundColor": "#0E1117",
        "allow_symbol_change": True,
        "hide_side_toolbar": False,
        "hide_top_toolbar": False,
        "withdateranges": True,
        "calendar": False,
        "support_host": "https://www.tradingview.com",
    }

    html = f"""
    <style>
      html, body {{ margin:0; padding:0; height:{H}px; background:#0E1117; }}
      .wrap {{ height:{H}px; width:100%; }}
      .wrap > div {{ height:100% !important; width:100% !important; }}
    </style>
    <div class="wrap tradingview-widget-container">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript"
        src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
        {json.dumps(cfg)}
      </script>
    </div>
    """
    components.html(html, height=H + 10)

    st.caption("Chart TradingView ka hai (spot XAUUSD/XAGUSD, OANDA feed). "
               "Model ka data futures (GC=F, SI=F) pe hai, isliye price me thoda "
               "farak aa sakta hai. Educational use only.")
