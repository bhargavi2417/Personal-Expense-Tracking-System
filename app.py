"""Personal Expense Tracking System - Flask application.

Run with:  python app.py   (then open http://127.0.0.1:5000 in Chrome)
"""
import calendar
import hmac
import secrets
from datetime import date

from flask import (Flask, Response, abort, flash, jsonify, redirect,
                   render_template, request, session, url_for)

from analysis import charts, reports, stats
from config import Config, config_problems_for_startup
from db import Database, DatabaseError, DatabaseUnavailable, IntegrityViolation
from repository import CategoryInUse, Repository
from validators import (validate_category, validate_expense, validate_filters,
                        validate_month)


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    db = Database(app.config)
    repo = Repository(db)
    app.extensions["expense_db"] = db
    app.extensions["expense_repo"] = repo

    # ------------------------------------------------------------------ helpers
    def csrf_token():
        if "_csrf" not in session:
            session["_csrf"] = secrets.token_hex(16)
        return session["_csrf"]

    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def csrf_protect():
        if request.method == "POST" and app.config.get("CSRF_ENABLED", True):
            sent = request.form.get("csrf_token", "")
            expected = session.get("_csrf", "")
            if not sent or not expected or not hmac.compare_digest(sent, expected):
                abort(400)

    @app.template_filter("money")
    def money(value):
        symbol = app.config.get("CURRENCY_SYMBOL", "Rs.")
        try:
            return "%s%s" % (symbol, format(float(value), ",.2f"))
        except (TypeError, ValueError):
            return "%s0.00" % symbol

    @app.template_filter("nice_date")
    def nice_date(value):
        try:
            return value.strftime("%d %b %Y")
        except AttributeError:
            return str(value)

    def category_ids():
        return [c["id"] for c in repo.list_categories()]

    def read_filters():
        """Valid filters from the query string; invalid ones are flashed and dropped."""
        filters, messages = validate_filters(request.args, category_ids())
        for message in messages:
            flash(message, "warning")
        return filters

    def filter_query(filters):
        args = {}
        if filters["start"]:
            args["start"] = filters["start"]
        if filters["end"]:
            args["end"] = filters["end"]
        if filters["category_id"]:
            args["category"] = filters["category_id"]
        return args

    # ------------------------------------------------------------------- pages
    @app.route("/")
    def dashboard():
        filters = read_filters()
        rows = repo.list_expenses(filters)
        df = stats.expenses_to_df(rows)
        return render_template(
            "dashboard.html",
            filters=filters,
            chart_args=filter_query(filters),
            categories=repo.list_categories(),
            summary=stats.summary_stats(df),
            breakdown=stats.category_breakdown(df),
            monthly=stats.monthly_totals(df),
            this_month=stats.month_total(df, date.today()),
            recent=rows[:5],
        )

    @app.route("/expenses")
    def expenses():
        filters = read_filters()
        rows = repo.list_expenses(filters)
        total = sum((r["amount"] for r in rows), start=0)
        return render_template("expenses.html", filters=filters, rows=rows, total=total,
                               categories=repo.list_categories(),
                               export_args=filter_query(filters))

    def _expense_form(mode, expense=None, form=None, errors=None, status=200):
        cats = repo.list_categories()
        if form is None:
            form = {}
            if expense:
                form = {"title": expense["title"], "amount": str(expense["amount"]),
                        "expense_date": expense["expense_date"].isoformat(),
                        "category_id": str(expense["category_id"]),
                        "notes": expense["notes"] or ""}
            else:
                form = {"expense_date": date.today().isoformat()}
        action = (url_for("add_expense") if mode == "add"
                  else url_for("edit_expense", expense_id=expense["id"]))
        return render_template("expense_form.html", mode=mode, form=form,
                               errors=errors or {}, categories=cats, action=action,
                               today=date.today().isoformat()), status

    @app.route("/expenses/add", methods=["GET", "POST"])
    def add_expense():
        if request.method == "GET":
            return _expense_form("add")
        clean, errors = validate_expense(request.form, category_ids())
        if errors:
            return _expense_form("add", form=request.form, errors=errors, status=400)
        repo.create_expense(clean)
        flash("Expense added.", "success")
        return redirect(url_for("expenses"))

    @app.route("/expenses/<int:expense_id>/edit", methods=["GET", "POST"])
    def edit_expense(expense_id):
        expense = repo.get_expense(expense_id)
        if expense is None:
            abort(404)
        if request.method == "GET":
            return _expense_form("edit", expense=expense)
        clean, errors = validate_expense(request.form, category_ids())
        if errors:
            return _expense_form("edit", expense=expense, form=request.form,
                                 errors=errors, status=400)
        repo.update_expense(expense_id, clean)
        flash("Expense updated.", "success")
        return redirect(url_for("expenses"))

    @app.route("/expenses/<int:expense_id>/delete", methods=["POST"])
    def delete_expense(expense_id):
        if repo.delete_expense(expense_id) == 0:
            abort(404)
        flash("Expense deleted.", "success")
        return redirect(url_for("expenses"))

    # --------------------------------------------------------------- categories
    @app.route("/categories", methods=["GET", "POST"])
    def categories():
        form, errors, status = {}, {}, 200
        if request.method == "POST":
            clean, errors = validate_category(request.form)
            if not errors and repo.category_name_taken(clean["name"]):
                errors["name"] = "A category with this name already exists."
            if errors:
                form, status = request.form, 400
            else:
                try:
                    repo.create_category(clean["name"], clean["description"])
                except IntegrityViolation:
                    flash("A category with this name already exists.", "error")
                    return redirect(url_for("categories"))
                flash("Category added.", "success")
                return redirect(url_for("categories"))
        return render_template("categories.html", categories=repo.list_categories(),
                               form=form, errors=errors), status

    @app.route("/categories/<int:category_id>/edit", methods=["POST"])
    def edit_category(category_id):
        if repo.get_category(category_id) is None:
            abort(404)
        clean, errors = validate_category(request.form)
        if not errors and repo.category_name_taken(clean["name"], exclude_id=category_id):
            errors["name"] = "A category with this name already exists."
        if errors:
            for message in errors.values():
                flash(message, "error")
            return redirect(url_for("categories"))
        repo.update_category(category_id, clean["name"], clean["description"])
        flash("Category updated.", "success")
        return redirect(url_for("categories"))

    @app.route("/categories/<int:category_id>/delete", methods=["POST"])
    def delete_category(category_id):
        if repo.get_category(category_id) is None:
            abort(404)
        try:
            repo.delete_category(category_id)
        except (CategoryInUse, IntegrityViolation):
            flash("This category still has expenses. Move or delete them first.", "error")
        else:
            flash("Category deleted.", "success")
        return redirect(url_for("categories"))

    # ------------------------------------------------------------------ reports
    @app.route("/reports")
    def reports_page():
        today = date.today()
        raw = request.args.get("month")
        parsed = validate_month(raw) if raw else (today.year, today.month)
        if parsed is None:
            flash("Month must look like 2026-10; showing the current month.", "warning")
            parsed = (today.year, today.month)
        year, month = parsed
        last_day = calendar.monthrange(year, month)[1]
        start = date(year, month, 1).isoformat()
        end = date(year, month, last_day).isoformat()
        rows = repo.list_expenses({"start": start, "end": end})
        report = reports.monthly_report(stats.expenses_to_df(rows), year, month)
        return render_template("reports.html", report=report,
                               month_value="%04d-%02d" % (year, month),
                               month_name=calendar.month_name[month],
                               start=start, end=end)

    @app.route("/export.csv")
    def export_csv():
        filters = read_filters()
        text = reports.expenses_csv(repo.list_expenses(filters))
        # utf-8-sig so Excel on Windows shows the rupee sign / accents correctly
        return Response(text.encode("utf-8-sig"), mimetype="text/csv",
                        headers={"Content-Disposition": "attachment; filename=expenses.csv"})

    # ------------------------------------------------------------------- charts
    def _png(data):
        return Response(data, mimetype="image/png",
                        headers={"Cache-Control": "no-store"})

    @app.route("/chart/category.png")
    def chart_category():
        df = stats.expenses_to_df(repo.list_expenses(read_filters()))
        return _png(charts.category_pie_png(stats.category_breakdown(df)))

    @app.route("/chart/monthly.png")
    def chart_monthly():
        df = stats.expenses_to_df(repo.list_expenses(read_filters()))
        return _png(charts.monthly_bar_png(stats.monthly_totals(df)))

    @app.route("/health")
    def health():
        try:
            counts = db.check()
        except DatabaseError as exc:
            return jsonify(status="error", message=str(exc)), 503
        return jsonify(status="ok", **counts)

    # ------------------------------------------------------------ error handlers
    @app.errorhandler(DatabaseUnavailable)
    def handle_db_unavailable(exc):
        return render_template("db_error.html", message=str(exc)), 503

    @app.errorhandler(DatabaseError)
    def handle_db_error(exc):
        return render_template("error.html", code=500, title="Database problem",
                               message=str(exc)), 500

    @app.errorhandler(400)
    def handle_400(exc):
        return render_template("error.html", code=400, title="Request not accepted",
                               message="The form may have expired. Go back, refresh "
                                       "the page and try again."), 400

    @app.errorhandler(404)
    def handle_404(exc):
        return render_template("error.html", code=404, title="Not found",
                               message="That page or record does not exist."), 404

    @app.errorhandler(500)
    def handle_500(exc):
        return render_template("error.html", code=500, title="Something went wrong",
                               message="An unexpected error occurred. Check the "
                                       "terminal window for details."), 500

    return app


if __name__ == "__main__":
    application = create_app()
    for problem in config_problems_for_startup(application.config):
        print("WARNING:", problem)
    print("Open http://127.0.0.1:5000 in Chrome. Press Ctrl+C to stop.")
    application.run(host="127.0.0.1", port=5000, debug=False)
