# Personal Expense Tracking System

A beginner-friendly web application to record, filter and analyse personal expenses.
Built with **Python, Flask, MySQL, HTML, CSS, JavaScript, Pandas, NumPy and Matplotlib**.

## Features

- Add, view, edit and delete expenses (amount must be greater than zero)
- Manage categories (add, rename, delete; a category that still has expenses cannot be deleted)
- Filter by date range, by category, or both together
- Dashboard: total, count, average, highest, this-month total, category totals with percentages,
  pie chart and monthly bar chart
- Monthly report (total, average, median, standard deviation, category breakdown, top 5 expenses)
- CSV download of the filtered expenses
- Friendly error messages for bad input and for database/configuration problems
- Automated tests (78 tests) and a database diagnostic command

## Project structure

```
Personal_Expense_Tracking_System/
  app.py             Flask application (routes)
  config.py          Settings read from .env
  db.py              Database connection helper (parameterized SQL only)
  repository.py      All SQL queries for categories and expenses
  validators.py      Input validation
  init_db.py         Creates the database/tables and loads sample data
  diagnose.py        Checks Python packages, .env and the MySQL connection
  schema.sql         MySQL tables
  sample_data.sql    Fictional sample categories and expenses
  .env.example       Template for your own MySQL settings
  requirements.txt   Python packages
  start_app.bat      Optional Windows launcher
  analysis/          stats.py (Pandas/NumPy), charts.py (Matplotlib), reports.py
  templates/         HTML pages (Jinja2)
  static/            css/style.css, js/app.js
  tests/             Automated tests
  docs/              Project report, presentation and notes
```

## Requirements

- Windows 10/11, **Python 3.10 or newer (64-bit)** - tick "Add python.exe to PATH" when installing
- **MySQL Server 8.0 or newer** (MySQL Installer from mysql.com) - remember the root password you choose
- Visual Studio Code and Google Chrome

## Setup on Windows (PowerShell)

### 1. Download and extract
Download `Personal_Expense_Tracking_System.zip`, right-click it > **Extract All...**
(for example to `C:\Projects`). You get the folder `C:\Projects\Personal_Expense_Tracking_System`.

### 2. Open the folder in Visual Studio Code
Start VS Code > **File > Open Folder...** > choose `Personal_Expense_Tracking_System`.
Open a terminal with **Terminal > New Terminal** (it is PowerShell and already inside the project folder).
**Run every command below from this project folder** (the folder that contains `app.py`).

Check that you are in the right place:
```powershell
dir app.py
```

### 3. Create a virtual environment
```powershell
python -m venv .venv
```

### 4. Activate it
```powershell
.\.venv\Scripts\Activate.ps1
```
If PowerShell says *"running scripts is disabled"*, run this once and try again:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```
You should now see `(.venv)` at the start of the prompt. If VS Code asks which Python interpreter to use, choose the one inside `.venv`.

### 5. Install the dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Make sure MySQL is running
Press **Win + R**, type `services.msc`, find **MySQL80** (or similar) and make sure it is *Running*.

### 7. Enter your MySQL settings
```powershell
Copy-Item .env.example .env
notepad .env
```
Change `DB_PASSWORD` to **your own MySQL root password** (and `DB_USER` if you use another user). Save and close.
The `.env` file stays on your computer only. Never share it.

### 8. Create the database and tables, and load sample data
```powershell
python init_db.py --sample
```
This creates the database `expense_tracker`, the tables, and ~34 fictional expenses.
It never deletes anything and skips the sample data if expenses already exist.
Use `python init_db.py` (without `--sample`) if you want an empty database.

*Alternative (MySQL Workbench):* open `schema.sql`, run it, then open `sample_data.sql` and run it **once**.

### 9. Verify the database
```powershell
python diagnose.py
```
You should see `[ OK ]` lines, including `Table 'expenses' exists: 34 row(s)`.
You can also check inside MySQL:
```sql
USE expense_tracker;
SHOW TABLES;
SELECT COUNT(*) FROM expenses;
```

### 10. Start the server
```powershell
python app.py
```
Or double-click `start_app.bat` (it only starts the app; it installs nothing).

### 11. Open the application in Chrome
Go to **http://127.0.0.1:5000**. Stop the server with **Ctrl + C** in the terminal.

### 12. Run the automated tests
Open a second terminal in the project folder, activate the environment (step 4), then:
```powershell
python -m unittest discover -s tests -t . -v
```
The tests use a temporary SQLite file, so your real MySQL data is never changed.

**Optional - tests against a real MySQL test database.** These are skipped unless you set:
```powershell
$env:TEST_DB_USER="root"
$env:TEST_DB_PASSWORD="your MySQL password"
$env:TEST_DB_NAME="expense_tracker_test"
python -m unittest discover -s tests -t . -v
```
The name must end in `_test`; the tests create that separate database and empty it before every test.

## Troubleshooting

| Problem | What to do |
|---|---|
| `python` is not recognised | Reinstall Python and tick "Add python.exe to PATH", then reopen VS Code. |
| `Activate.ps1 cannot be loaded` | Run the `Set-ExecutionPolicy` command in step 4. |
| `ModuleNotFoundError: No module named 'flask'` | The environment is not active or packages are missing: do steps 4 and 5. |
| Page says "database is not ready" | Run `python diagnose.py` and fix the `[FAIL]` lines. |
| `Access denied for user` | Wrong `DB_USER` / `DB_PASSWORD` in `.env`. |
| `Cannot reach the MySQL server` | Start the MySQL service (step 6); check `DB_HOST` and `DB_PORT`. |
| `Unknown database 'expense_tracker'` | Run `python init_db.py`. |
| `Port 5000 is already in use` | Close the other program, or change the port at the bottom of `app.py`. |
| Sample data was skipped | Expenses already exist; that is intended. |
| Changed `.env` but nothing changed | Stop the server (Ctrl+C) and start it again. |

## Security notes

- All SQL uses parameterized queries; HTML output is escaped; forms use CSRF tokens.
- No passwords are stored in the project. `.env` is listed in `.gitignore`.
- The server binds to `127.0.0.1` (only your own computer can open it). It is a demo/learning setup, not a production deployment.
