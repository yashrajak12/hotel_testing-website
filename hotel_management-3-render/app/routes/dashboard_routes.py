from flask import Blueprint, render_template, request, flash
from flask_login import login_required
from ..extensions import db
from ..models.order import Order
from ..models.employee import Employee
from ..models.billing import Bill
from datetime import date, datetime

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    # Get filter parameters (same as billing_routes.py and order_routes.py)
    filter_date_str = request.args.get('date')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    # Initialize query
    order_query = Order.query
    bill_query = Bill.query

    # Single date filter (highest priority)
    if filter_date_str:
        try:
            filter_date = datetime.strptime(filter_date_str, '%Y-%m-%d').date()
            order_query = order_query.filter(db.func.date(Order.created_at) == filter_date)
            bill_query = bill_query.filter(db.func.date(Bill.generated_at) == filter_date)
        except ValueError:
            flash('Invalid single date format!', 'danger')

    # Date range filter (only if no single date)
    elif start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            if start_date > end_date:
                flash('From date cannot be after To date!', 'danger')
            else:
                order_query = order_query.filter(db.func.date(Order.created_at).between(start_date, end_date))
                bill_query = bill_query.filter(db.func.date(Bill.generated_at).between(start_date, end_date))
        except ValueError:
            flash('Invalid date range format!', 'danger')

    # Default: today
    else:
        today = date.today()
        order_query = order_query.filter(db.func.date(Order.created_at) == today)
        bill_query = bill_query.filter(db.func.date(Bill.generated_at) == today)

    # Calculate stats
    total_orders_count = order_query.count()

    live_orders_count = order_query.filter(
        Order.status.notin_(['Paid', 'Served'])
    ).count()

    employees_count = Employee.query.count()

    # Revenue from filtered bills
    bills = bill_query.all()
    total_revenue = sum(b.grand_total or 0 for b in bills)
    cash_revenue = sum(b.grand_total or 0 for b in bills if b.payment_mode == 'Cash')
    online_revenue = sum(b.grand_total or 0 for b in bills if b.payment_mode == 'Online')

    # Recent orders (latest first, limited)
    recent_orders = order_query.order_by(Order.created_at.desc()).limit(8).all()

    # Add temporary day_sequence for display
    for index, order in enumerate(recent_orders, start=1):
        order.day_sequence = index

    # Render template
    return render_template(
        'dashboard/index.html',
        total_orders_count=total_orders_count,
        live_orders_count=live_orders_count,
        employees_count=employees_count,
        total_revenue=total_revenue,
        cash_revenue=cash_revenue,
        online_revenue=online_revenue,
        recent_orders=recent_orders
        # We don't need to pass selected_date/start_date/end_date anymore
        # because the template now uses request.args.get() directly
    )