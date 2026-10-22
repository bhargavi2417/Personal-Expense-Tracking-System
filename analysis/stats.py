"""Statistics with Pandas and NumPy. All functions are safe for empty data."""
import numpy as np
import pandas as pd


def expenses_to_df(rows):
    """Convert repository rows to a DataFrame (empty-safe, correct dtypes)."""
    if not rows:
        return pd.DataFrame({
            "id": pd.Series(dtype="int64"),
            "title": pd.Series(dtype="object"),
            "amount": pd.Series(dtype="float64"),
            "expense_date": pd.Series(dtype="datetime64[ns]"),
            "category": pd.Series(dtype="object"),
        })
    df = pd.DataFrame({
        "id": [int(r["id"]) for r in rows],
        "title": [r["title"] for r in rows],
        "amount": [float(r["amount"]) for r in rows],
        "expense_date": pd.to_datetime([r["expense_date"] for r in rows]),
        "category": [r["category_name"] for r in rows],
    })
    return df


def summary_stats(df):
    if df.empty:
        return {"total": 0.0, "count": 0, "average": 0.0, "median": 0.0,
                "highest": 0.0, "lowest": 0.0, "std_dev": 0.0}
    a = df["amount"].to_numpy(dtype=float)
    return {
        "total": round(float(np.sum(a)), 2),
        "count": int(a.size),
        "average": round(float(np.mean(a)), 2),
        "median": round(float(np.median(a)), 2),
        "highest": round(float(np.max(a)), 2),
        "lowest": round(float(np.min(a)), 2),
        "std_dev": round(float(np.std(a, ddof=1)), 2) if a.size > 1 else 0.0,
    }


def category_breakdown(df):
    """List of {category, total, count, percent}, biggest first."""
    if df.empty:
        return []
    grouped = df.groupby("category", as_index=False).agg(
        total=("amount", "sum"), count=("id", "count"))
    grand = float(grouped["total"].sum())
    grouped = grouped.sort_values(["total", "category"], ascending=[False, True])
    result = []
    for _, row in grouped.iterrows():
        total = float(row["total"])
        result.append({
            "category": str(row["category"]),
            "total": round(total, 2),
            "count": int(row["count"]),
            "percent": round(total / grand * 100, 2) if grand > 0 else 0.0,
        })
    return result


def monthly_totals(df):
    """List of {month: 'YYYY-MM', total, count}, oldest first."""
    if df.empty:
        return []
    keys = df["expense_date"].dt.strftime("%Y-%m")
    grouped = df.groupby(keys).agg(total=("amount", "sum"), count=("id", "count"))
    return [{"month": str(month), "total": round(float(row["total"]), 2),
             "count": int(row["count"])}
            for month, row in grouped.sort_index().iterrows()]


def filter_month(df, year, month):
    """Rows of ``df`` that fall in the given calendar month."""
    if df.empty:
        return df
    mask = (df["expense_date"].dt.year == year) & (df["expense_date"].dt.month == month)
    return df[mask]


def month_total(df, today):
    return summary_stats(filter_month(df, today.year, today.month))["total"]


def top_expenses(df, n=5):
    if df.empty:
        return []
    top = df.sort_values(["amount", "expense_date"], ascending=[False, False]).head(n)
    return [{"title": str(r["title"]), "amount": round(float(r["amount"]), 2),
             "date": r["expense_date"].date(), "category": str(r["category"])}
            for _, r in top.iterrows()]
