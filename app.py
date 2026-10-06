import os
from calendar import monthrange
from datetime import date
from decimal import Decimal, InvalidOperation

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user

from models import Budget, Transaction, User, db

TRANSACTION_TYPES = ("INCOME", "EXPENSE")
CATEGORIES = ("Food", "Transport", "Shopping", "Bills", "Entertainment", "Health", "Education", "Salary", "Other")

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///expense_tracker.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.cli.command("init-db")
def init_db():
    with app.app_context():
        db.create_all()
    print("Database initialized.")


@app.route("/")
def index():
    return redirect(url_for("dashboard" if current_user.is_authenticated else "login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Name, email, and a password of at least 8 characters are required.", "danger")
        elif db.session.scalar(db.select(User).where(User.email == email)):
            flash("An account with that email already exists.", "danger")
        else:
            user = User(name=name, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = db.session.scalar(db.select(User).where(User.email == email))
        if user and user.check_password(request.form.get("password", "")):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@app.get("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.get("/dashboard")
@login_required
def dashboard():
    today = date.today()
    selected_month = request.args.get("month", "")
    try:
        year, month = (int(part) for part in selected_month.split("-"))
        if not 1 <= month <= 12 or not 2000 <= year <= 2100:
            raise ValueError
    except (ValueError, TypeError):
        year, month = today.year, today.month
        selected_month = f"{year:04d}-{month:02d}"

    user_filter = Transaction.user_id == current_user.id
    user_transactions = db.session.scalars(db.select(Transaction).where(user_filter)).all()
    total_income = sum((t.amount for t in user_transactions if t.type == "INCOME"), Decimal("0"))
    total_expenses = sum((t.amount for t in user_transactions if t.type == "EXPENSE"), Decimal("0"))
    month_transactions = [t for t in user_transactions if t.date.year == year and t.date.month == month]
    monthly_income = sum((t.amount for t in month_transactions if t.type == "INCOME"), Decimal("0"))
    monthly_expense_total = sum((t.amount for t in month_transactions if t.type == "EXPENSE"), Decimal("0"))
    budget = db.session.scalar(db.select(Budget).where(
        Budget.user_id == current_user.id, Budget.month == month, Budget.year == year))
    budget_amount = budget.amount if budget else Decimal("0")
    budget_remaining = budget_amount - monthly_expense_total
    budget_percent = (monthly_expense_total / budget_amount * 100) if budget_amount else Decimal("0")

    category_totals = {}
    for transaction in user_transactions:
        if transaction.type == "EXPENSE":
            category_totals[transaction.category] = category_totals.get(transaction.category, Decimal("0")) + transaction.amount

    monthly_expenses = []
    for offset in range(5, -1, -1):
        month_index = today.month - offset
        chart_year = today.year + (month_index - 1) // 12
        chart_month = (month_index - 1) % 12 + 1
        amount = sum((t.amount for t in user_transactions
                      if t.type == "EXPENSE" and t.date.year == chart_year and t.date.month == chart_month), Decimal("0"))
        monthly_expenses.append({"label": f"{chart_year}-{chart_month:02d}", "amount": float(amount)})

    return render_template(
        "dashboard_phase4.html", total_income=total_income, total_expenses=total_expenses,
        balance=total_income - total_expenses, transaction_count=len(user_transactions),
        recent_transactions=sorted(user_transactions, key=lambda t: (t.date, t.id), reverse=True)[:5],
        monthly_income=monthly_income, monthly_expenses=monthly_expense_total,
        budget_amount=budget_amount, budget_spent=monthly_expense_total,
        budget_remaining=budget_remaining, budget_percent=min(float(budget_percent), 100),
        selected_month=selected_month, category_labels=list(category_totals),
        category_values=[float(value) for value in category_totals.values()],
        monthly_chart=monthly_expenses,
    )


@app.route("/budget", methods=["GET", "POST"])
@login_required
def budget():
    today = date.today()
    selected_month = request.values.get("month", f"{today.year:04d}-{today.month:02d}")
    try:
        year, month = (int(part) for part in selected_month.split("-"))
        if not 1 <= month <= 12 or not 2000 <= year <= 2100:
            raise ValueError
    except (ValueError, TypeError):
        year, month = today.year, today.month
        selected_month = f"{year:04d}-{month:02d}"
    current_budget = db.session.scalar(db.select(Budget).where(
        Budget.user_id == current_user.id, Budget.month == month, Budget.year == year))
    if request.method == "POST":
        try:
            amount = Decimal(request.form.get("amount", "").strip())
            if amount < 0:
                raise InvalidOperation
        except (InvalidOperation, AttributeError):
            flash("Budget must be zero or a valid positive amount.", "danger")
        else:
            if current_budget:
                current_budget.amount = amount
            else:
                db.session.add(Budget(user_id=current_user.id, month=month, year=year, amount=amount))
            db.session.commit()
            flash("Monthly budget saved.", "success")
            return redirect(url_for("budget", month=selected_month))
    spent = sum((t.amount for t in db.session.scalars(db.select(Transaction).where(
        Transaction.user_id == current_user.id, Transaction.type == "EXPENSE",
        Transaction.date >= date(year, month, 1),
        Transaction.date <= date(year, month, monthrange(year, month)[1]))).all()), Decimal("0"))
    amount = current_budget.amount if current_budget else Decimal("0")
    percent = float(spent / amount * 100) if amount else 0
    return render_template("budget.html", selected_month=selected_month, budget_amount=amount,
                           spent=spent, remaining=amount - spent, percent=min(percent, 100))


def transaction_form_data(form):
    try:
        amount = Decimal(form.get("amount", "").strip())
    except (InvalidOperation, AttributeError):
        return None, "Amount must be a valid number."
    transaction_type = form.get("type", "").strip().upper()
    category = form.get("category", "").strip()
    try:
        transaction_date = date.fromisoformat(form.get("date", "").strip())
    except ValueError:
        return None, "Please provide a valid date."
    if amount <= 0:
        return None, "Amount must be greater than zero."
    if transaction_type not in TRANSACTION_TYPES:
        return None, "Choose a valid transaction type."
    if category not in CATEGORIES:
        return None, "Choose a valid category."
    return {"amount": amount, "type": transaction_type, "category": category,
            "description": form.get("description", "").strip(), "date": transaction_date}, None


@app.get("/transactions")
@login_required
def transactions():
    query = db.select(Transaction).where(Transaction.user_id == current_user.id)
    selected_type = request.args.get("type", "").upper()
    selected_category = request.args.get("category", "")
    if selected_type in TRANSACTION_TYPES:
        query = query.where(Transaction.type == selected_type)
    else:
        selected_type = ""
    if selected_category in CATEGORIES:
        query = query.where(Transaction.category == selected_category)
    else:
        selected_category = ""
    page = db.paginate(query.order_by(Transaction.date.desc(), Transaction.id.desc()), per_page=10)
    return render_template("transactions.html", transactions=page, categories=CATEGORIES,
                           selected_type=selected_type, selected_category=selected_category)


@app.route("/transactions/add", methods=["GET", "POST"])
@login_required
def add_transaction():
    if request.method == "POST":
        values, error = transaction_form_data(request.form)
        if error:
            flash(error, "danger")
        else:
            db.session.add(Transaction(user_id=current_user.id, **values))
            db.session.commit()
            flash("Transaction added successfully.", "success")
            return redirect(url_for("transactions"))
    return render_template("transaction_form.html", transaction=None, categories=CATEGORIES,
                           transaction_types=TRANSACTION_TYPES, today=date.today().isoformat())


@app.route("/transactions/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_transaction(id):
    transaction = db.session.scalar(db.select(Transaction).where(
        Transaction.id == id, Transaction.user_id == current_user.id))
    if transaction is None:
        flash("Transaction not found.", "danger")
        return redirect(url_for("transactions"))
    if request.method == "POST":
        values, error = transaction_form_data(request.form)
        if error:
            flash(error, "danger")
        else:
            for key, value in values.items():
                setattr(transaction, key, value)
            db.session.commit()
            flash("Transaction updated successfully.", "success")
            return redirect(url_for("transactions"))
    return render_template("transaction_form.html", transaction=transaction, categories=CATEGORIES,
                           transaction_types=TRANSACTION_TYPES, today=date.today().isoformat())


@app.post("/transactions/delete/<int:id>")
@login_required
def delete_transaction(id):
    transaction = db.session.scalar(db.select(Transaction).where(
        Transaction.id == id, Transaction.user_id == current_user.id))
    if transaction is None:
        flash("Transaction not found.", "danger")
    else:
        db.session.delete(transaction)
        db.session.commit()
        flash("Transaction deleted.", "success")
    return redirect(url_for("transactions"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
