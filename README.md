# Expense Tracker & Finance Dashboard

An approachable personal-finance dashboard for recording income and expenses, tracking monthly budgets, and understanding spending with responsive charts. Built as a clean GitHub/resume project using server-rendered Flask templates.

## Features

- Secure registration, login, logout, and Werkzeug password hashing
- User-isolated transaction CRUD with validation, filters, and pagination
- Income, expenses, balance, recent activity, and monthly summaries
- Chart.js income/expense, category, and six-month spending charts
- Monthly budgets with spent, remaining, percentage-used, progress colors, and warnings

## Tech stack

Python 3.11+, Flask, Flask-SQLAlchemy, SQLite, Flask-Login, Bootstrap 5, Chart.js, and vanilla JavaScript.

## Screenshots

Add screenshots of the dashboard, transactions page, and budget page here.

## Project structure

`app.py` contains routes and application configuration. `models.py` contains the User, Transaction, and Budget models. HTML lives in `templates/`, with CSS and dashboard JavaScript under `static/`.

## Phase 1 setup

1. Create and activate a virtual environment: `python -m venv .venv` then `.venv\\Scripts\\activate` on Windows.
2. Install dependencies: `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and replace `SECRET_KEY` with a long random value.
4. Initialize the database: `flask --app app init-db`.
5. Run: `flask --app app run --debug`.

## Database

SQLite is used by default and is created at runtime as `expense_tracker.db`. Run `flask --app app init-db` after installation. Set `DATABASE_URL` in `.env` to use another SQLAlchemy-compatible database URL.

## Environment configuration

Copy `.env.example` to `.env` and set a long random `SECRET_KEY`. `.env` is ignored by Git; never commit real secrets.

## Future improvements

CSV export, recurring transactions, automated tests, and optional database migrations.
