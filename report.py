import io
from datetime import datetime
import pandas as pd
from fpdf import FPDF


def clean(s):
    # fpdf ke default font me emoji / special symbols nahi chalte
    return str(s).encode("latin-1", "replace").decode("latin-1")


def make_chart(gold, silver):
    """gold, silver: 1-D pandas Series (index = time)"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 3))
    ax.plot(gold.index, gold.values, color="goldenrod", label="Gold")
    ax.set_ylabel("Gold (USD)")
    ax2 = ax.twinx()
    ax2.plot(silver.index, silver.values, color="gray", label="Silver")
    ax2.set_ylabel("Silver (USD)")
    ax.set_title("Gold vs Silver")
    fig.autofmt_xdate()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def build_pdf(prices, preds, pt_summary, events_df=None, chart=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    def h(text):
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 9, clean(text), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)

    def line(text):
        pdf.cell(0, 6, clean(text), new_x="LMARGIN", new_y="NEXT")

    # Title
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, "GoldSilver AI - Research Report", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    line(f"Generated: {datetime.now():%Y-%m-%d %H:%M}")
    pdf.ln(4)

    # Prices + predictions
    h("1. Latest Prices and ML Predictions")
    for a in ["Gold", "Silver"]:
        p = preds.get(a, {})
        line(f"{a}: latest ${prices[a]:,.2f} | next-hour est. "
             f"${p.get('next', 0):,.2f} | direction: {p.get('direction', '-')}")
    pdf.ln(3)

    # Chart
    if chart is not None:
        h("2. Price Chart")
        pdf.image(chart, w=180)
        pdf.ln(3)

    # Paper trading
    h("3. Paper Trading Summary")
    line(f"Cash: ${pt_summary['cash']:,.2f}")
    line(f"Total equity: ${pt_summary['equity']:,.2f} ({pt_summary['return_pct']:.2f}%)")
    line(f"Realized P&L: ${pt_summary['realized']:,.2f}")
    line(f"Unrealized P&L: ${pt_summary['unrealized']:,.2f}")
    line(f"Total trades: {pt_summary['trades']}")
    pdf.ln(3)

    # Events
    h("4. Upcoming Economic Events")
    if events_df is not None and not events_df.empty:
        for _, r in events_df.iterrows():
            line(f"{r['date']} | {r['country']} | {r['impact']} | {r['event']}")
    else:
        line("No upcoming events available.")
    pdf.ln(3)

    # Disclaimer
    h("Disclaimer")
    pdf.multi_cell(0, 5, clean(
        "Educational research report. Predictions are estimates, not guaranteed "
        "trading signals. Paper trading uses virtual money. Not financial advice."),
        new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())
