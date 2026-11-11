import json
import pandas as pd
import streamlit as st

FEE = 0.0005          # 0.05% transaction cost
SLIPPAGE = 0.0002     # 0.02% slippage
START_CASH = 100000.0
ASSETS = ["Gold", "Silver"]


def init_state():
    if "pt" not in st.session_state:
        st.session_state.pt = {
            "cash": START_CASH,
            "pos": {a: 0.0 for a in ASSETS},
            "avg": {a: 0.0 for a in ASSETS},
            "realized": 0.0,
            "log": [],
            "equity": [],
        }


def portfolio_value(prices):
    pt = st.session_state.pt
    return pt["cash"] + sum(pt["pos"][a] * prices[a] for a in ASSETS)


def execute(asset, side, qty, price):
    pt = st.session_state.pt
    if qty <= 0:
        return False, "Quantity 0 se zyada honi chahiye"

    if side == "BUY":
        px = price * (1 + SLIPPAGE)
        value = qty * px
        fee = value * FEE
        if pt["cash"] < value + fee:
            return False, "Cash kam hai"
        old_q = pt["pos"][asset]
        new_q = old_q + qty
        pt["avg"][asset] = (pt["avg"][asset] * old_q + px * qty) / new_q
        pt["pos"][asset] = new_q
        pt["cash"] -= value + fee
    else:
        px = price * (1 - SLIPPAGE)
        value = qty * px
        fee = value * FEE
        if pt["pos"][asset] < qty:
            return False, "Itni quantity holding me nahi hai"
        pt["realized"] += (px - pt["avg"][asset]) * qty - fee
        pt["pos"][asset] -= qty
        pt["cash"] += value - fee
        if pt["pos"][asset] < 1e-9:
            pt["pos"][asset] = 0.0
            pt["avg"][asset] = 0.0

    pt["log"].append({
        "time": str(pd.Timestamp.now().floor("s")),
        "asset": asset, "side": side, "qty": qty,
        "price": round(px, 4), "fee": round(fee, 4),
    })
    return True, f"{side} {qty} {asset} @ ${px:,.2f} (fee ${fee:,.2f})"


def summary(prices):
    """PDF report ke liye summary dict"""
    init_state()
    pt = st.session_state.pt
    equity = portfolio_value(prices)
    unreal = sum((prices[a] - pt["avg"][a]) * pt["pos"][a] for a in ASSETS)
    return {
        "cash": pt["cash"], "equity": equity,
        "return_pct": (equity / START_CASH - 1) * 100,
        "realized": pt["realized"], "unrealized": unreal,
        "trades": len(pt["log"]),
    }


def render(prices, signals=None):
    init_state()
    pt = st.session_state.pt

    st.subheader("Paper Trading Simulator")
    st.caption(f"Virtual balance ${START_CASH:,.0f} | Fee {FEE*100:.2f}% | "
               f"Slippage {SLIPPAGE*100:.2f}% | Long-only (short selling nahi)")

    if signals:
        st.info(" | ".join(f"{a}: model signal **{s}**" for a, s in signals.items()))

    # --- Trade controls ---
    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
    asset = c1.selectbox("Asset", ASSETS, key="pt_asset")
    qty = c2.number_input("Quantity", min_value=0.0, value=1.0, step=1.0, key="pt_qty")
    c3.write("")
    c4.write("")
    buy = c3.button("BUY", key="pt_buy", use_container_width=True)
    sell = c4.button("SELL", key="pt_sell", use_container_width=True)

    if buy or sell:
        ok, msg = execute(asset, "BUY" if buy else "SELL", qty, prices[asset])
        (st.success if ok else st.error)(msg)

    # --- Metrics (trade ke BAAD calculate hote hain) ---
    equity = portfolio_value(prices)
    if not pt["equity"] or pt["equity"][-1]["equity"] != round(equity, 2):
        pt["equity"].append({"time": str(pd.Timestamp.now().floor("s")),
                             "equity": round(equity, 2)})

    m1, m2, m3 = st.columns(3)
    m1.metric("Cash", f"${pt['cash']:,.2f}")
    m2.metric("Total Equity", f"${equity:,.2f}", f"{(equity/START_CASH-1)*100:.2f}%")
    m3.metric("Realized P&L", f"${pt['realized']:,.2f}")

    # --- Positions ---
    rows = []
    for a in ASSETS:
        q, avg, px = pt["pos"][a], pt["avg"][a], prices[a]
        rows.append({"Asset": a, "Qty": q, "Avg Price": round(avg, 2),
                     "Current": round(px, 2), "Value": round(q * px, 2),
                     "Unrealized P&L": round((px - avg) * q, 2)})
    st.write("**Positions**")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # --- Equity curve + log ---
    if len(pt["equity"]) > 1:
        st.write("**Equity curve**")
        eq = pd.DataFrame(pt["equity"]).set_index("time")
        st.line_chart(eq)
    if pt["log"]:
        st.write("**Trade log**")
        st.dataframe(pd.DataFrame(pt["log"]).iloc[::-1],
                     use_container_width=True, hide_index=True)

    # --- Save / Load / Reset ---
    st.write("**Portfolio save / load**")
    st.download_button("Download portfolio (JSON)", json.dumps(pt, indent=2),
                       "portfolio.json", "application/json", key="pt_dl")
    up = st.file_uploader("Upload portfolio", type="json", key="pt_up")
    if up is not None and st.button("Load portfolio", key="pt_load"):
        st.session_state.pt = json.load(up)
        st.rerun()
    if st.button("Reset portfolio", key="pt_reset"):
        del st.session_state["pt"]
        st.rerun()
