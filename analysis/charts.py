"""Matplotlib charts returned as PNG bytes.

Figures are created with matplotlib.figure.Figure (not pyplot), so no global
state is kept and nothing leaks between requests. Each figure is garbage
collected after the PNG bytes are produced.
"""
from io import BytesIO

from matplotlib.figure import Figure

PALETTE = ["#4f46e5", "#06b6d4", "#10b981", "#f59e0b", "#ef4444",
           "#8b5cf6", "#ec4899", "#14b8a6", "#64748b", "#84cc16"]


def _to_png(fig):
    buf = BytesIO()
    try:
        fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
        return buf.getvalue()
    finally:
        buf.close()


def _empty_chart(message="No data to display"):
    fig = Figure(figsize=(6, 4))
    ax = fig.subplots()
    ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=14, color="#6b7280")
    ax.set_axis_off()
    return _to_png(fig)


def category_pie_png(breakdown):
    """``breakdown`` is the list from stats.category_breakdown."""
    if not breakdown:
        return _empty_chart()
    labels = [b["category"] for b in breakdown]
    values = [b["total"] for b in breakdown]
    fig = Figure(figsize=(6.5, 4.5))
    ax = fig.subplots()
    colors = [PALETTE[i % len(PALETTE)] for i in range(len(values))]
    wedges, _texts, autotexts = ax.pie(
        values, colors=colors, startangle=90, counterclock=False,
        autopct=lambda pct: "%.1f%%" % pct if pct >= 4 else "",
        pctdistance=0.75, wedgeprops={"edgecolor": "white"},
        textprops={"color": "white", "fontsize": 9})
    ax.legend(wedges, ["%s (%.1f%%)" % (b["category"], b["percent"]) for b in breakdown],
              loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False, fontsize=9)
    ax.set_title("Spending by category")
    ax.axis("equal")
    return _to_png(fig)


def monthly_bar_png(monthly, currency="Rs."):
    """``monthly`` is the list from stats.monthly_totals."""
    if not monthly:
        return _empty_chart()
    months = [m["month"] for m in monthly]
    totals = [m["total"] for m in monthly]
    fig = Figure(figsize=(6, 4.5))
    ax = fig.subplots()
    bars = ax.bar(months, totals, color=PALETTE[0])
    ax.set_title("Monthly spending")
    ax.set_xlabel("Month")
    ax.set_ylabel("Total (%s)" % currency)
    ax.bar_label(bars, labels=["{:,.0f}".format(t) for t in totals], padding=2, fontsize=8)
    ax.tick_params(axis="x", labelrotation=45)
    ax.margins(y=0.12)
    return _to_png(fig)
