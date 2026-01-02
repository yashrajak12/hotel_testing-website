from flask import Blueprint, render_template, request, flash
from flask_login import login_required
from ..extensions import db
from ..models.billing import Bill
from ..models.inventory import Expense
from datetime import datetime, date
from sqlalchemy import func
from ..routes.decorators import role_required
from decimal import Decimal

report_bp = Blueprint('report', __name__, url_prefix='/reports')

@report_bp.route('/dashboard')
@login_required
@role_required('Admin', 'Manager')
def dashboard():
    filter_date_str = request.args.get('date')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    today = date.today()
    start_date = today
    end_date = today

    if filter_date_str:
        try:
            dt = datetime.strptime(filter_date_str, '%Y-%m-%d').date()
            start_date = end_date = dt
            flash(f"Showing data for {dt.strftime('%d %b %Y')}", 'info')
        except ValueError:
            flash('Invalid single date format!', 'danger')

    elif start_date_str and end_date_str:
        try:
            s = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            e = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            if s > e:
                flash('From date cannot be after To date!', 'danger')
            else:
                start_date = s
                end_date = e
                flash(f"Showing data from {s.strftime('%d %b %Y')} to {e.strftime('%d %b %Y')}", 'info')
        except ValueError:
            flash('Invalid date range format!', 'danger')

    else:
        flash(f"Showing data for today - {today.strftime('%d %b %Y')}", 'info')

    # Fetch filtered data
    bills = Bill.query.filter(func.date(Bill.generated_at).between(start_date, end_date)).all()
    inventory_expenses = Expense.query.filter(func.date(Expense.date).between(start_date, end_date)).all()

    # Force everything to Decimal — prevents float/Decimal mismatch
    def to_decimal(value):
        if value is None:
            return Decimal('0')
        if isinstance(value, (int, float)):
            return Decimal(str(value))  # safe conversion from float
        return value  # already Decimal

    total_revenue = Decimal('0')
    cash_revenue = Decimal('0')
    online_revenue = Decimal('0')

    for bill in bills:
        amount = to_decimal(bill.grand_total)
        total_revenue += amount
        if bill.payment_mode == 'Cash':
            cash_revenue += amount
        elif bill.payment_mode == 'Online':
            online_revenue += amount

    monthly_expenses = Decimal('0')
    for exp in inventory_expenses:
        monthly_expenses += to_decimal(exp.payment_amount)

    # Now both are Decimal → safe subtraction
    profit_loss = total_revenue - monthly_expenses

    # Recent data
    recent_bills = Bill.query.filter(func.date(Bill.generated_at).between(start_date, end_date)) \
                             .order_by(Bill.generated_at.desc()) \
                             .limit(10).all()

    recent_expenses = Expense.query.filter(func.date(Expense.date).between(start_date, end_date)) \
                                   .order_by(Expense.date.desc()) \
                                   .limit(10).all()

    for index, bill in enumerate(recent_bills, start=1):
        bill.day_sequence = index

    return render_template(
        'reports/dashboard.html',
        total_revenue=total_revenue,
        cash_revenue=cash_revenue,
        online_revenue=online_revenue,
        monthly_expenses=monthly_expenses,
        profit_loss=profit_loss,
        recent_bills=recent_bills,
        recent_expenses=recent_expenses
    )