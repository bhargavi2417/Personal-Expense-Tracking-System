# Testing notes

Run: `python -m unittest discover -s tests -t . -v`

| File | What it covers |
|---|---|
| test_validators.py | amount, date, title, category, filter and month validation |
| test_expenses.py | create, list, edit, delete, positive amount, required fields, invalid input, escaping |
| test_categories.py | add, rename, duplicate names, delete rules |
| test_filters_and_analysis.py | date / category / combined filters, dashboard totals vs SQL SUM, monthly totals, category percentages, empty data, charts, CSV |
| test_errors_and_config.py | missing .env values, 404, CSRF, database failure pages, /health |
| test_static_review.py | syntax, imports, templates, url_for endpoints, static files, forms, schema consistency, sample data |
| test_mysql_integration.py | the same CRUD/filter/analysis tests on a real MySQL test database (skipped unless TEST_DB_* are set) |

Normal runs use SQLite in a temporary folder. MySQL-specific behaviour is only covered by the optional integration tests.
