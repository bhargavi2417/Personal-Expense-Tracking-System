import unittest
from decimal import Decimal

from tests.base import AppTestCase


class ExpenseTests(AppTestCase):
    def setUp(self):
        super().setUp()
        self.cat = self.make_category("Food")

    def test_create_and_list(self):
        r = self.client.post("/expenses/add", data=self.form(self.cat))
        self.assertEqual(r.status_code, 302)
        rows = self.repo.list_expenses()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["title"], "Tea")
        self.assertEqual(rows[0]["amount"], Decimal("25.50"))
        page = self.client.get("/expenses")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"Tea", page.data)
        self.assertIn(b"Rs.25.50", page.data)

    def test_edit(self):
        eid = self.make_expense(self.cat, title="Old", amount="10.00")
        form_page = self.client.get("/expenses/%d/edit" % eid)
        self.assertEqual(form_page.status_code, 200)
        self.assertIn(b"Old", form_page.data)
        r = self.client.post("/expenses/%d/edit" % eid,
                             data=self.form(self.cat, title="New", amount="99.99"))
        self.assertEqual(r.status_code, 302)
        row = self.repo.get_expense(eid)
        self.assertEqual((row["title"], row["amount"]), ("New", Decimal("99.99")))

    def test_edit_missing_expense_is_404(self):
        self.assertEqual(self.client.get("/expenses/9999/edit").status_code, 404)
        self.assertEqual(self.client.post("/expenses/9999/edit",
                                          data=self.form(self.cat)).status_code, 404)

    def test_delete(self):
        eid = self.make_expense(self.cat)
        r = self.client.post("/expenses/%d/delete" % eid)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self.repo.list_expenses(), [])
        self.assertEqual(self.client.post("/expenses/%d/delete" % eid).status_code, 404)

    def test_delete_requires_post(self):
        eid = self.make_expense(self.cat)
        self.assertEqual(self.client.get("/expenses/%d/delete" % eid).status_code, 405)

    def test_amount_must_be_positive(self):
        for bad in ["0", "-1", "-0.50", "abc", "", "1.999"]:
            r = self.client.post("/expenses/add", data=self.form(self.cat, amount=bad))
            self.assertEqual(r.status_code, 400, bad)
        self.assertEqual(self.repo.list_expenses(), [])

    def test_amount_message_is_shown(self):
        r = self.client.post("/expenses/add", data=self.form(self.cat, amount="-5"))
        self.assertIn(b"Amount must be greater than zero.", r.data)

    def test_required_fields(self):
        r = self.client.post("/expenses/add", data={})
        self.assertEqual(r.status_code, 400)
        for text in (b"Title is required.", b"Amount is required.",
                     b"Date is required.", b"Please choose a category."):
            self.assertIn(text, r.data)

    def test_form_keeps_entered_values_on_error(self):
        r = self.client.post("/expenses/add",
                             data=self.form(self.cat, title="Keep me", amount="-1"))
        self.assertIn(b"Keep me", r.data)

    def test_invalid_inputs_do_not_crash(self):
        for overrides in ({"expense_date": "not-a-date"}, {"category_id": "abc"},
                          {"category_id": "9999"}, {"title": "x" * 500},
                          {"expense_date": "2999-01-01"}):
            r = self.client.post("/expenses/add", data=self.form(self.cat, **overrides))
            self.assertEqual(r.status_code, 400, overrides)

    def test_future_date_rejected(self):
        r = self.client.post("/expenses/add",
                             data=self.form(self.cat, expense_date="2999-01-01"))
        self.assertIn(b"cannot be in the future", r.data)

    def test_sql_injection_text_is_stored_as_plain_text(self):
        evil = "x'); DROP TABLE expenses;--"
        self.client.post("/expenses/add", data=self.form(self.cat, title=evil))
        self.assertEqual(self.repo.list_expenses()[0]["title"], evil)
        self.assertEqual(self.db.check()["expenses"], 1)

    def test_html_is_escaped(self):
        self.client.post("/expenses/add", data=self.form(self.cat, title="<script>alert(1)</script>"))
        page = self.client.get("/expenses")
        self.assertNotIn(b"<script>alert(1)</script>", page.data)
        self.assertIn(b"&lt;script&gt;", page.data)

    def test_empty_list_page(self):
        self.repo.delete_category  # touch
        page = self.client.get("/expenses")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"No expenses found", page.data)

    def test_add_page_without_categories(self):
        self.db.execute("DELETE FROM categories")
        page = self.client.get("/expenses/add")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"at least one category", page.data)


if __name__ == "__main__":
    unittest.main()
