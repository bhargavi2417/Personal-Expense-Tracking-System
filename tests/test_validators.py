import unittest
from datetime import date
from decimal import Decimal

from tests.base import PROJECT_DIR  # noqa: F401  (sets sys.path)
from validators import (parse_amount, validate_category, validate_expense,
                        validate_filters, validate_month)

TODAY = date(2026, 10, 22)


def good(**kw):
    data = {"title": "Tea", "amount": "25.50", "expense_date": "2026-10-01",
            "category_id": "1", "notes": ""}
    data.update(kw)
    return data


class AmountTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(parse_amount("25.5")[0], Decimal("25.50"))
        self.assertEqual(parse_amount("1,250.00")[0], Decimal("1250.00"))

    def test_invalid_values(self):
        for bad in ["", "   ", "abc", "0", "0.00", "-5", "-0.01", "NaN", "Infinity",
                    "1.234", "100000000", "1e400"]:
            value, error = parse_amount(bad)
            self.assertIsNone(value, bad)
            self.assertTrue(error, bad)


class ExpenseValidationTests(unittest.TestCase):
    def test_all_good(self):
        clean, errors = validate_expense(good(), [1], today=TODAY)
        self.assertEqual(errors, {})
        self.assertEqual(clean["amount"], Decimal("25.50"))
        self.assertEqual(clean["expense_date"], date(2026, 10, 1))
        self.assertIsNone(clean["notes"])

    def test_required_fields(self):
        _, errors = validate_expense({}, [1], today=TODAY)
        self.assertEqual(set(errors), {"title", "amount", "expense_date", "category_id"})

    def test_whitespace_title_rejected(self):
        _, errors = validate_expense(good(title="   "), [1], today=TODAY)
        self.assertIn("title", errors)

    def test_long_title_and_notes(self):
        _, errors = validate_expense(good(title="x" * 101, notes="y" * 501), [1], today=TODAY)
        self.assertIn("title", errors)
        self.assertIn("notes", errors)

    def test_bad_dates(self):
        for bad in ["31-10-2026", "2026-02-30", "yesterday", "1999-12-31", "2026-10-23"]:
            _, errors = validate_expense(good(expense_date=bad), [1], today=TODAY)
            self.assertIn("expense_date", errors, bad)

    def test_today_is_allowed(self):
        _, errors = validate_expense(good(expense_date="2026-10-22"), [1], today=TODAY)
        self.assertEqual(errors, {})

    def test_category_checks(self):
        for bad in ["", "abc", "99"]:
            _, errors = validate_expense(good(category_id=bad), [1], today=TODAY)
            self.assertIn("category_id", errors, bad)


class OtherValidationTests(unittest.TestCase):
    def test_category(self):
        clean, errors = validate_category({"name": "  Food   Court ", "description": ""})
        self.assertEqual(errors, {})
        self.assertEqual(clean["name"], "Food Court")
        self.assertIn("name", validate_category({"name": ""})[1])
        self.assertIn("name", validate_category({"name": "x" * 51})[1])

    def test_filters(self):
        f, msgs = validate_filters({"start": "2026-01-01", "end": "2026-02-01", "category": "1"}, [1])
        self.assertEqual((f["start"], f["end"], f["category_id"]), ("2026-01-01", "2026-02-01", 1))
        self.assertEqual(msgs, [])
        f, msgs = validate_filters({"start": "2026-03-01", "end": "2026-02-01"}, [1])
        self.assertIsNone(f["start"])
        self.assertTrue(msgs)
        f, msgs = validate_filters({"start": "nonsense", "category": "zzz"}, [1])
        self.assertEqual(len(msgs), 2)
        f, msgs = validate_filters({"category": "7"}, [1])
        self.assertIsNone(f["category_id"])

    def test_month(self):
        self.assertEqual(validate_month("2026-10"), (2026, 10))
        for bad in ["2026-13", "2026-00", "26-10", "", None, "2026-1"]:
            self.assertIsNone(validate_month(bad))


if __name__ == "__main__":
    unittest.main()
