"""Input validation. Every function returns (clean_values, errors) so the
web layer can show understandable messages instead of crashing."""
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

MAX_AMOUNT = Decimal("99999999.99")
MIN_DATE = date(2000, 1, 1)
_MONTH_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")


def parse_date(text):
    """Parse YYYY-MM-DD. Returns a date or None."""
    try:
        return datetime.strptime((text or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_amount(text):
    """Return (Decimal | None, error | None)."""
    raw = (text or "").strip().replace(",", "")
    if not raw:
        return None, "Amount is required."
    try:
        value = Decimal(raw)
    except InvalidOperation:
        return None, "Amount must be a number, for example 250.50."
    if not value.is_finite():
        return None, "Amount must be a normal number."
    if value <= 0:
        return None, "Amount must be greater than zero."
    if value > MAX_AMOUNT:
        return None, "Amount is too large (maximum 99,999,999.99)."
    rounded = value.quantize(Decimal("0.01"))
    if value != rounded:
        return None, "Amount can have at most 2 decimal places."
    return rounded, None


def validate_expense(form, valid_category_ids, today=None):
    today = today or date.today()
    errors = {}
    clean = {}

    title = (form.get("title") or "").strip()
    if not title:
        errors["title"] = "Title is required."
    elif len(title) > 100:
        errors["title"] = "Title must be 100 characters or fewer."
    clean["title"] = title

    amount, amount_error = parse_amount(form.get("amount"))
    if amount_error:
        errors["amount"] = amount_error
    clean["amount"] = amount

    raw_date = (form.get("expense_date") or "").strip()
    parsed = parse_date(raw_date)
    if not raw_date:
        errors["expense_date"] = "Date is required."
    elif parsed is None:
        errors["expense_date"] = "Date must look like 2026-10-31."
    elif parsed < MIN_DATE:
        errors["expense_date"] = "Date cannot be before 2000-01-01."
    elif parsed > today:
        errors["expense_date"] = "Date cannot be in the future."
    clean["expense_date"] = parsed

    raw_cat = (form.get("category_id") or "").strip()
    category_id = None
    if not raw_cat:
        errors["category_id"] = "Please choose a category."
    else:
        try:
            category_id = int(raw_cat)
        except ValueError:
            errors["category_id"] = "Please choose a valid category."
        else:
            if category_id not in set(valid_category_ids):
                errors["category_id"] = "That category does not exist."
    clean["category_id"] = category_id

    notes = (form.get("notes") or "").strip()
    if len(notes) > 500:
        errors["notes"] = "Notes must be 500 characters or fewer."
    clean["notes"] = notes or None
    return clean, errors


def validate_category(form):
    errors = {}
    name = " ".join((form.get("name") or "").split())
    if not name:
        errors["name"] = "Category name is required."
    elif len(name) > 50:
        errors["name"] = "Category name must be 50 characters or fewer."
    description = (form.get("description") or "").strip()
    if len(description) > 255:
        errors["description"] = "Description must be 255 characters or fewer."
    return {"name": name, "description": description or None}, errors


def validate_filters(args, valid_category_ids):
    """Read ?start=&end=&category= from the query string.

    Returns (filters, error_messages). ``filters`` only contains valid values.
    """
    filters = {"start": None, "end": None, "category_id": None}
    messages = []

    start_raw = (args.get("start") or "").strip()
    end_raw = (args.get("end") or "").strip()
    cat_raw = (args.get("category") or "").strip()

    if start_raw:
        start = parse_date(start_raw)
        if start is None:
            messages.append("Start date must look like 2026-10-31; it was ignored.")
        else:
            filters["start"] = start.isoformat()
    if end_raw:
        end = parse_date(end_raw)
        if end is None:
            messages.append("End date must look like 2026-10-31; it was ignored.")
        else:
            filters["end"] = end.isoformat()
    if filters["start"] and filters["end"] and filters["start"] > filters["end"]:
        messages.append("Start date is after the end date, so both dates were ignored.")
        filters["start"] = filters["end"] = None
    if cat_raw:
        try:
            cat_id = int(cat_raw)
        except ValueError:
            messages.append("Category filter was not valid and was ignored.")
        else:
            if cat_id in set(valid_category_ids):
                filters["category_id"] = cat_id
            else:
                messages.append("That category does not exist; the filter was ignored.")
    return filters, messages


def validate_month(text):
    """Return (year, month) for 'YYYY-MM', or None if invalid."""
    match = _MONTH_RE.match((text or "").strip())
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))
