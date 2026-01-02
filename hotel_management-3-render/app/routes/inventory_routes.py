from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from ..extensions import db
from ..models.inventory import Inventory, Expense, InventoryCategory, InventoryStatus, PaymentMode
from datetime import datetime, date
from sqlalchemy import func
from ..routes.decorators import role_required

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@inventory_bp.route('/')
@login_required
@role_required('Admin', 'Manager')
def list():
    # Date filter
    filter_date_str = request.args.get('date')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    query = Expense.query.join(Inventory)

    if filter_date_str:
        try:
            filter_date = datetime.strptime(filter_date_str, '%Y-%m-%d').date()
            query = query.filter(func.date(Expense.date) == filter_date)
        except ValueError:
            flash('Invalid date!', 'danger')
    elif start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            query = query.filter(func.date(Expense.date).between(start_date, end_date))
        except ValueError:
            flash('Invalid date range!', 'danger')

    expenses = query.order_by(Expense.date.desc()).all()

    # Group by item
    grouped_items = {}
    for expense in expenses:
        item = expense.inventory
        if item.item_id not in grouped_items:
            grouped_items[item.item_id] = {
                'item': item,
                'expenses': []
            }
        grouped_items[item.item_id]['expenses'].append(expense)

    today = date.today()

    return render_template('inventory/list.html', grouped_items=grouped_items.values(), today=today, request=request)

@inventory_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Manager')
def add():
    if request.method == 'POST':
        name = request.form.get('name')
        category_str = request.form.get('category')
        quantity_with_unit = request.form.get('quantity_with_unit')
        payment_amount_str = request.form.get('payment_amount')
        payment_mode_str = request.form.get('payment_mode', 'CASH')

        if not all([name, category_str, quantity_with_unit, payment_amount_str]):
            flash('All fields required!', 'danger')
            return redirect(url_for('inventory.add'))

        try:
            payment_amount = float(payment_amount_str)
            category_enum = InventoryCategory(category_str.upper())
            payment_mode_enum = PaymentMode(payment_mode_str.upper())
        except ValueError:
            flash('Invalid data!', 'danger')
            return redirect(url_for('inventory.add'))

        new_item = Inventory(
            item_name=name,
            category=category_enum,
            quantity_with_unit=quantity_with_unit
        )
        db.session.add(new_item)
        db.session.flush()

        expense = Expense(
            item_id=new_item.item_id,
            added_quantity_with_unit=quantity_with_unit,
            payment_amount=payment_amount,
            payment_mode=payment_mode_enum
        )
        db.session.add(expense)
        db.session.commit()

        flash('Item added successfully!', 'success')
        return redirect(url_for('inventory.list'))

    return render_template('inventory/add.html', categories=InventoryCategory, payment_modes=PaymentMode)

@inventory_bp.route('/add_quantity/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Manager')
def add_quantity(id):
    item = Inventory.query.get_or_404(id)
    if request.method == 'POST':
        added_qty = request.form.get('added_quantity_with_unit')
        payment_amount_str = request.form.get('payment_amount')
        payment_mode_str = request.form.get('payment_mode', 'CASH')

        if not all([added_qty, payment_amount_str]):
            flash('Quantity and payment required!', 'danger')
            return redirect(url_for('inventory.add_quantity', id=id))

        try:
            payment_amount = float(payment_amount_str)
            payment_mode_enum = PaymentMode(payment_mode_str.upper())
        except ValueError:
            flash('Invalid data!', 'danger')
            return redirect(url_for('inventory.add_quantity', id=id))

        # Update total quantity with history
        item.quantity_with_unit = f"{item.quantity_with_unit} + {added_qty}"

        # Save new addition in history
        expense = Expense(
            item_id=item.item_id,
            added_quantity_with_unit=added_qty,
            payment_amount=payment_amount,
            payment_mode=payment_mode_enum
        )
        db.session.add(expense)
        db.session.commit()

        flash('Quantity added successfully!', 'success')
        return redirect(url_for('inventory.list'))

    return render_template('inventory/add_quantity.html', item=item, payment_modes=PaymentMode)

@inventory_bp.route('/update_status/<int:id>', methods=['POST'])
@login_required
@role_required('Admin', 'Manager')
def update_status(id):
    item = Inventory.query.get_or_404(id)
    new_status = request.form.get('status')

    try:
        item.status = InventoryStatus(new_status.upper())
        db.session.commit()
        flash('Status updated!', 'success')
    except ValueError:
        flash('Invalid status!', 'danger')

    return redirect(url_for('inventory.list'))

@inventory_bp.route('/view/<int:id>')
@login_required
@role_required('Admin', 'Manager')
def view(id):
    item = Inventory.query.get_or_404(id)
    expenses = Expense.query.filter_by(item_id=id).order_by(Expense.date.desc()).all()
    total_expense = sum(e.payment_amount for e in expenses)
    return render_template('inventory/view.html', item=item, expenses=expenses, total_expense=total_expense)

@inventory_bp.route('/view_all')
@login_required
@role_required('Admin', 'Manager')
def view_all():
    items = Inventory.query.order_by(Inventory.created_at.desc()).all()
    for item in items:
        item.last_expense = Expense.query.filter_by(item_id=item.item_id).order_by(Expense.date.desc()).first()
        item.total_expense = sum(e.payment_amount for e in item.expenses)
    return render_template('inventory/view_all.html', items=items)