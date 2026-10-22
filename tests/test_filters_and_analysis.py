import unittest
from datetime import date
from decimal import Decimal

from analysis import charts, reports, stats
from tests.base import AppTestCase


class FilterTests(AppTestCase):
    def setUp(self):
        super().setUp()
        self.food = self.make_category("Food")
        self.travel = self.make_category("Travel")
        self.make_expense(self.food, "A", "100.00", "2026-08-05")
        self.make_expense(self.travel, "B", "250.00", "2026-08-20")
        self.make_expense(self.food, "C", "50.00", "2026-09-02")
        self.make_expense(self.travel, "D", "75.25", "2026-09-15")

    def titles(self, filters):
        return sorted(r["title"] for r in self.repo.list_expenses(filters))

    def test_no_filter(self):
        self.assertEqual(self.titles({}), ["A", "B", "C", "D"])

    def test_date_only(self):
        self.assertEqual(self.titles({"start": "2026-08-10", "end": "2026-09-10"}), ["B", "C"])
        self.assertEqual(self.titles({"start": "2026-09-01"}), ["C", "D"])
        self.assertEqual(self.titles({"end": "2026-08-20"}), ["A", "B"])

    def test_date_bounds_are_inclusive(self):
        self.assertEqual(self.titles({"start": "2026-08-05", "end": "2026-08-05"}), ["A"])

    def test_category_only(self):
        self.assertEqual(self.titles({"category_id": self.food}), ["A", "C"])

    def test_combined(self):
        self.assertEqual(self.titles({"start": "2026-08-01", "end": "2026-08-31",
                                      "category_id": self.travel}), ["B"])
        self.assertEqual(self.titles({"start": "2026-10-01", "category_id": self.food}), [])

    def test_filters_through_web_pages(self):
        r = self.client.get("/expenses?start=2026-08-01&end=2026-08-31&category=%d" % self.travel)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"250.00", r.data)
        self.assertNotIn(b"75.25", r.data)

    def test_bad_filter_values_do_not_crash(self):
        for qs in ("start=abc", "end=2026-13-45", "category=xyz", "category=999",
                   "start=2026-09-01&end=2026-08-01"):
            for path in ("/", "/expenses", "/export.csv", "/chart/category.png"):
                self.assertEqual(self.client.get("%s?%s" % (path, qs)).status_code, 200, (path, qs))

    def test_dashboard_total_matches_database(self):
        for filters in ({}, {"category_id": self.food},
                        {"start": "2026-09-01", "end": "2026-09-30"},
                        {"start": "2026-08-01", "end": "2026-08-31", "category_id": self.food}):
            rows = self.repo.list_expenses(filters)
            summary = stats.summary_stats(stats.expenses_to_df(rows))
            self.assertEqual(Decimal(str(summary["total"])), self.repo.total_amount(filters))
            self.assertEqual(summary["count"], len(rows))
        page = self.client.get("/")
        self.assertIn(b"Rs.475.25", page.data)


class AnalysisTests(AppTestCase):
    def setUp(self):
        super().setUp()
        self.food = self.make_category("Food")
        self.travel = self.make_category("Travel")
        self.make_expense(self.food, "A", "100.00", "2026-08-05")
        self.make_expense(self.travel, "B", "300.00", "2026-08-20")
        self.make_expense(self.food, "C", "100.00", "2026-09-02")
        self.df = stats.expenses_to_df(self.repo.list_expenses())

    def test_summary(self):
        s = stats.summary_stats(self.df)
        self.assertEqual((s["total"], s["count"], s["highest"], s["lowest"]), (500.0, 3, 300.0, 100.0))
        self.assertEqual(s["average"], 166.67)
        self.assertEqual(s["median"], 100.0)

    def test_monthly_totals(self):
        self.assertEqual(stats.monthly_totals(self.df), [
            {"month": "2026-08", "total": 400.0, "count": 2},
            {"month": "2026-09", "total": 100.0, "count": 1}])

    def test_category_totals_and_percentages(self):
        b = stats.category_breakdown(self.df)
        self.assertEqual([(x["category"], x["total"], x["percent"]) for x in b],
                         [("Travel", 300.0, 60.0), ("Food", 200.0, 40.0)])
        self.assertAlmostEqual(sum(x["percent"] for x in b), 100.0, places=1)

    def test_month_total_and_filter(self):
        self.assertEqual(stats.month_total(self.df, date(2026, 8, 31)), 400.0)
        self.assertEqual(stats.month_total(self.df, date(2026, 12, 1)), 0.0)
        self.assertEqual(len(stats.filter_month(self.df, 2026, 9)), 1)

    def test_monthly_report(self):
        rep = reports.monthly_report(self.df, 2026, 8)
        self.assertEqual(rep["summary"]["total"], 400.0)
        self.assertEqual(rep["top"][0]["title"], "B")
        self.assertEqual(rep["categories"][0]["category"], "Travel")

    def test_reports_page(self):
        page = self.client.get("/reports?month=2026-08")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"Rs.400.00", page.data)
        self.assertEqual(self.client.get("/reports?month=2026-8").status_code, 200)
        self.assertEqual(self.client.get("/reports?month=garbage").status_code, 200)
        empty = self.client.get("/reports?month=2020-01")
        self.assertIn(b"No expenses recorded", empty.data)

    def test_percent_with_many_categories_sums_to_about_100(self):
        for i in range(7):
            cid = self.make_category("Cat%d" % i)
            self.make_expense(cid, "x", "33.33", "2026-09-%02d" % (i + 1))
        b = stats.category_breakdown(stats.expenses_to_df(self.repo.list_expenses()))
        self.assertAlmostEqual(sum(x["percent"] for x in b), 100.0, delta=0.05 * len(b))


class EmptyDataTests(AppTestCase):
    def test_numpy_pandas_helpers_handle_empty(self):
        df = stats.expenses_to_df([])
        self.assertEqual(stats.summary_stats(df)["total"], 0.0)
        self.assertEqual(stats.summary_stats(df)["std_dev"], 0.0)
        self.assertEqual(stats.category_breakdown(df), [])
        self.assertEqual(stats.monthly_totals(df), [])
        self.assertEqual(stats.top_expenses(df), [])
        self.assertEqual(stats.month_total(df, date(2026, 1, 1)), 0.0)
        self.assertEqual(reports.monthly_report(df, 2026, 1)["summary"]["count"], 0)

    def test_single_row_std_dev_is_zero(self):
        cid = self.make_category("Food")
        self.make_expense(cid)
        s = stats.summary_stats(stats.expenses_to_df(self.repo.list_expenses()))
        self.assertEqual(s["std_dev"], 0.0)

    def test_all_pages_work_with_empty_database(self):
        for path in ("/", "/expenses", "/expenses/add", "/categories", "/reports",
                     "/export.csv", "/chart/category.png", "/chart/monthly.png", "/health"):
            self.assertEqual(self.client.get(path).status_code, 200, path)
        self.assertIn(b"No expenses match", self.client.get("/").data)

    def test_empty_charts_are_valid_png(self):
        for data in (charts.category_pie_png([]), charts.monthly_bar_png([])):
            self.assertTrue(data.startswith(b"\x89PNG"))


class ChartAndExportTests(AppTestCase):
    def test_charts_render_png_and_no_figure_leak(self):
        import matplotlib.pyplot as plt  # only to count pyplot-managed figures
        cid = self.make_category("Food")
        self.make_expense(cid, "A", "10.00", "2026-08-05")
        before = len(plt.get_fignums())
        for _ in range(5):
            for path in ("/chart/category.png", "/chart/monthly.png"):
                r = self.client.get(path)
                self.assertEqual(r.status_code, 200)
                self.assertEqual(r.mimetype, "image/png")
                self.assertTrue(r.data.startswith(b"\x89PNG"))
        self.assertEqual(len(plt.get_fignums()), before)

    def test_csv_export_and_formula_protection(self):
        cid = self.make_category("Food")
        self.make_expense(cid, "=HYPERLINK(\"x\")", "10.00", "2026-08-05", "ok, with comma")
        r = self.client.get("/export.csv")
        self.assertEqual(r.status_code, 200)
        self.assertIn("attachment", r.headers["Content-Disposition"])
        text = r.data.decode("utf-8-sig")
        self.assertTrue(text.startswith("ID,Date,Title,Category,Amount,Notes"))
        self.assertIn("'=HYPERLINK", text)
        self.assertIn("10.00", text)


if __name__ == "__main__":
    unittest.main()
