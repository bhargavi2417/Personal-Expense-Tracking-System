"""Optional integration tests against a REAL MySQL *test* database.

They are skipped unless you set these environment variables (PowerShell):

    $env:TEST_DB_USER="root"
    $env:TEST_DB_PASSWORD="your password"
    $env:TEST_DB_NAME="expense_tracker_test"     # must end with _test

The test database is created by the tests and emptied before every test.
Your real database (expense_tracker) is never touched.
"""
from tests import test_categories as _cat
from tests import test_expenses as _exp
from tests import test_filters_and_analysis as _fil


class MySQLExpenseTests(_exp.ExpenseTests):
    backend = "mysql"


class MySQLCategoryTests(_cat.CategoryTests):
    backend = "mysql"


class MySQLFilterTests(_fil.FilterTests):
    backend = "mysql"


class MySQLAnalysisTests(_fil.AnalysisTests):
    backend = "mysql"
