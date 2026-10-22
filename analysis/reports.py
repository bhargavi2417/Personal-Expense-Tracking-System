"""Report helpers: monthly report data and CSV export."""
import csv
import io

from . import stats

_CSV_DANGEROUS = ("=", "+", "-", "@", "\t", "\r")


def _safe_cell(value):
    """Stop spreadsheet formula injection when the CSV is opened in Excel."""
    text = "" if value is None else str(value)
    return "'" + text if text.startswith(_CSV_DANGEROUS) else text


def expenses_csv(rows):
    """Return CSV text for repository rows."""
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["ID", "Date", "Title", "Category", "Amount", "Notes"])
    for r in rows:
        writer.writerow([r["id"], r["expense_date"].isoformat(), _safe_cell(r["title"]),
                         _safe_cell(r["category_name"]), "%.2f" % r["amount"],
                         _safe_cell(r["notes"])])
    return out.getvalue()


def monthly_report(df, year, month):
    """Summary, category breakdown and top expenses for one month."""
    month_df = stats.filter_month(df, year, month)
    return {
        "year": year,
        "month": month,
        "summary": stats.summary_stats(month_df),
        "categories": stats.category_breakdown(month_df),
        "top": stats.top_expenses(month_df, 5),
    }
