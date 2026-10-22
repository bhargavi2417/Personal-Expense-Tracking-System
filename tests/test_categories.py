import unittest

from tests.base import AppTestCase


class CategoryTests(AppTestCase):
    def test_add_and_list(self):
        r = self.client.post("/categories", data={"name": "Travel", "description": "Trips"})
        self.assertEqual(r.status_code, 302)
        page = self.client.get("/categories")
        self.assertIn(b"Travel", page.data)
        self.assertEqual([c["name"] for c in self.repo.list_categories()], ["Travel"])

    def test_name_required_and_duplicates_rejected(self):
        self.assertEqual(self.client.post("/categories", data={"name": " "}).status_code, 400)
        self.client.post("/categories", data={"name": "Travel"})
        r = self.client.post("/categories", data={"name": "travel"})  # different case
        self.assertEqual(r.status_code, 400)
        self.assertIn(b"already exists", r.data)
        self.assertEqual(len(self.repo.list_categories()), 1)

    def test_rename(self):
        cid = self.make_category("Old")
        self.client.post("/categories/%d/edit" % cid, data={"name": "New", "description": "d"})
        self.assertEqual(self.repo.get_category(cid)["name"], "New")

    def test_rename_to_existing_name_rejected(self):
        a = self.make_category("A")
        self.make_category("B")
        self.client.post("/categories/%d/edit" % a, data={"name": "B"})
        self.assertEqual(self.repo.get_category(a)["name"], "A")

    def test_rename_keeping_same_name_is_allowed(self):
        a = self.make_category("A")
        self.client.post("/categories/%d/edit" % a, data={"name": "A", "description": "new text"})
        self.assertEqual(self.repo.get_category(a)["description"], "new text")

    def test_delete_unused(self):
        cid = self.make_category("Temp")
        self.client.post("/categories/%d/delete" % cid)
        self.assertEqual(self.repo.list_categories(), [])

    def test_cannot_delete_category_with_expenses(self):
        cid = self.make_category("Food")
        self.make_expense(cid)
        r = self.client.post("/categories/%d/delete" % cid, follow_redirects=True)
        self.assertIn(b"still has expenses", r.data)
        self.assertEqual(len(self.repo.list_categories()), 1)
        self.assertEqual(len(self.repo.list_expenses()), 1)

    def test_expense_count_shown(self):
        cid = self.make_category("Food")
        self.make_expense(cid)
        self.make_expense(cid)
        self.assertEqual(self.repo.list_categories()[0]["expense_count"], 2)

    def test_missing_category_is_404(self):
        self.assertEqual(self.client.post("/categories/999/delete").status_code, 404)
        self.assertEqual(self.client.post("/categories/999/edit", data={"name": "x"}).status_code, 404)


if __name__ == "__main__":
    unittest.main()
