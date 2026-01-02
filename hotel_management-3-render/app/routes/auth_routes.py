from datetime import date

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user

from ..models.billing import Bill
from ..models.employee import Employee
from ..models.order import Order
from ..models.user import User, Role
from ..extensions import db

auth_bp = Blueprint('auth', __name__, url_prefix='')

# ROOT ROUTE - App khulte hi direct SIGNUP page dikhega
@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))  # Dashboard route ka endpoint
    return redirect(url_for('auth.signup'))         # Pehle signup dikhao (development ke liye)

# SIGNUP ROUTE - PUBLIC (koi login required nahi)
@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        role_str = request.form.get('role')

        print(f"Form Data: username={username}, role={role_str}")  # Debug ke liye

        if not all([username, password, confirm_password, role_str]):
            flash('All fields are required!', 'danger')
            return render_template('auth/signup.html')

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('auth/signup.html')

        if User.query.filter_by(username=username).first():
            flash('Username already taken!', 'danger')
            return render_template('auth/signup.html')

        try:
            # Role ko properly convert karo
            role = Role[role_str.upper()]  # ADMIN, MANAGER etc.
            new_user = User(username=username, role=role)
            new_user.set_password(password)

            db.session.add(new_user)
            db.session.commit()

            flash(f'Success! "{username}" registered as {role.value}. Now login below.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            print(f"Error: {e}")  # Console mein error dikhega
            flash(f'Error: {str(e)}', 'danger')  # User ko bhi dikhao
            return render_template('auth/signup.html')

    return render_template('auth/signup.html')

# LOGIN ROUTE
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome {username}! Logged in as {user.role.value}', 'success')
            return redirect(url_for('auth.dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('auth/login.html')


# DASHBOARD
from datetime import datetime, date
from flask import request
@auth_bp.route('/dashboard')
@login_required
def dashboard():
    # Date filter logic
    filter_date_str = request.args.get('date')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    if filter_date_str:
        try:
            selected_date = datetime.strptime(filter_date_str, '%Y-%m-%d').date()
            start_date = end_date = selected_date
        except:
            flash('Invalid date!', 'danger')
            start_date = end_date = date.today()
    elif start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except:
            flash('Invalid date range!', 'danger')
            start_date = end_date = date.today()
    else:
        start_date = end_date = date.today()

    # Orders in selected period
    orders_query = Order.query.filter(db.func.date(Order.created_at).between(start_date, end_date))

    total_orders_count = orders_query.count()

    live_orders_count = orders_query.filter(Order.status.notin_(['Paid', 'Served'])).count()

    # Revenue from Bills
    bills_query = Bill.query.filter(db.func.date(Bill.generated_at).between(start_date, end_date))
    bills = bills_query.all()

    total_revenue = sum(bill.grand_total for bill in bills)
    cash_revenue = sum(bill.grand_total for bill in bills if bill.payment_mode == 'Cash')
    online_revenue = sum(bill.grand_total for bill in bills if bill.payment_mode == 'Online')

    # Recent orders with day-wise sequence
    recent_orders = orders_query.order_by(Order.created_at.asc()).all()
    for index, order in enumerate(recent_orders, start=1):
        order.day_sequence = index

    # Total employee
    employees_count = Employee.query.count()  # ← Ab error nahi aayega

    return render_template('dashboard/index.html',
                           total_orders_count=total_orders_count,
                           live_orders_count=live_orders_count,
                           employees_count=employees_count,
                           total_revenue=total_revenue,
                           cash_revenue=cash_revenue,
                           online_revenue=online_revenue,
                           recent_orders=recent_orders,
                           selected_date=start_date if start_date == end_date else None,
                           start_date=start_date,
                           end_date=end_date)
# LOGOUT
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'info')
    return redirect(url_for('auth.login'))