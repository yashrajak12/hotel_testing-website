from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from ..extensions import db
from ..models.billing import Bill
from ..models.order import Order, OrderItem, OrderStatus
from ..models.menu import Category, MenuItem
from ..routes.decorators import role_required

order_bp = Blueprint('order', __name__, url_prefix='/orders')

# All routes must be defined BEFORE blueprint registration

from datetime import datetime, date
from flask import request  # ← add this import

@order_bp.route('/')
@login_required
def list():
    filter_date_str = request.args.get('date')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    query = Order.query

    if filter_date_str:
        try:
            filter_date = datetime.strptime(filter_date_str, '%Y-%m-%d').date()
            query = query.filter(db.func.date(Order.created_at) == filter_date)
        except:
            flash('Invalid date format!', 'danger')
    elif start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            query = query.filter(db.func.date(Order.created_at).between(start_date, end_date))
        except:
            flash('Invalid date range!', 'danger')
    else:
        today = date.today()
        query = query.filter(db.func.date(Order.created_at) == today)

    # Ascending order (oldest first)
    orders = query.order_by(Order.created_at.asc()).all()

    # Add day-wise sequential number
    for index, order in enumerate(orders, start=1):
        order.day_sequence = index  # Temporary attribute for template

    return render_template('orders/list.html', orders=orders)

@order_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('Waiter', 'Cashier', 'Admin', 'Manager')
def add():
    if request.method == 'POST':
        order_type = request.form['order_type']
        table_number = request.form.get('table_number') if order_type == 'Dine-in' else None
        customer_name = request.form.get('customer_name') if order_type == 'Parcel' else None

        if order_type == 'Dine-in' and not table_number:
            flash('Table number is required for Dine-in!', 'danger')
            categories = Category.query.order_by(Category.name).all()
            return render_template('orders/add.html', categories=categories)

        if order_type == 'Parcel' and not customer_name:
            flash('Customer name is required for Parcel!', 'danger')
            categories = Category.query.order_by(Category.name).all()
            return render_template('orders/add.html', categories=categories)

        order = Order(
            order_type=order_type,
            table_number=table_number,
            customer_name=customer_name,
            status=OrderStatus.PENDING
        )
        db.session.add(order)
        db.session.flush()

        total = 0.0
        items_added = False
        for key in request.form:
            if key.startswith('qty_'):
                item_id = key.split('_')[1]
                qty = int(request.form.get(key, 0))
                if qty > 0:
                    item = MenuItem.query.get(item_id)
                    if item and item.available:
                        order_item = OrderItem(
                            order_id=order.id,
                            menu_item_id=item.id,
                            quantity=qty,
                            price_at_time=item.price,
                            added_after_edit=0
                        )
                        db.session.add(order_item)
                        total += qty * item.price
                        items_added = True

        if not items_added:
            db.session.rollback()
            flash('Please select at least one item!', 'danger')
            categories = Category.query.order_by(Category.name).all()
            return render_template('orders/add.html', categories=categories)

        order.total_amount = total
        db.session.commit()
        flash(f'Order #{order.id} placed successfully! Total: ₹{total}', 'success')
        return redirect(url_for('order.list'))

    categories = Category.query.order_by(Category.name).all()
    return render_template('orders/add.html', categories=categories)

@order_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('Waiter', 'Cashier', 'Admin', 'Manager')
def edit(id):
    order = Order.query.get_or_404(id)
    if request.method == 'POST':
        order.edit_count += 1
        order.status = f"Partial {order.edit_count}"

        added_total = 0.0
        for key in request.form:
            if key.startswith('qty_'):
                item_id = key.split('_')[1]
                qty = int(request.form.get(key, 0))
                if qty > 0:
                    item = MenuItem.query.get(item_id)
                    if item and item.available:
                        # Check if already exists
                        existing = OrderItem.query.filter_by(order_id=order.id, menu_item_id=item.id).first()
                        if existing:
                            existing.quantity += qty
                        else:
                            new_item = OrderItem(
                                order_id=order.id,
                                menu_item_id=item.id,
                                quantity=qty,
                                price_at_time=item.price,
                                added_after_edit=order.edit_count
                            )
                            db.session.add(new_item)
                        added_total += qty * item.price

        order.total_amount += added_total
        db.session.commit()
        flash(f'Order edited! Now status: Partial {order.edit_count}', 'success')
        return redirect(url_for('order.list'))

    categories = Category.query.order_by(Category.name).all()
    return render_template('orders/edit.html', order=order, categories=categories)

@order_bp.route('/update_status/<int:id>', methods=['POST'])
@login_required
@role_required('Chef', 'Admin', 'Manager')
def update_status(id):
    order = Order.query.get_or_404(id)
    new_status = request.form['status']
    if new_status in ['Pending', 'Preparing', 'Ready', 'Served']:
        order.status = new_status
        db.session.commit()
        flash('Status updated!', 'success')
    else:
        flash('Invalid status!', 'danger')
    return redirect(url_for('order.list'))


from datetime import datetime, timezone  # ← yahan bhi import


@order_bp.route('/mark_paid/<int:id>', methods=['POST'])
@login_required
@role_required('Cashier', 'Admin', 'Manager')
def mark_paid(id):
    order = Order.query.get_or_404(id)

    if order.is_paid:
        flash('Order already paid!', 'info')
        return redirect(url_for('order.list'))

    payment_mode = request.form.get('payment_mode')
    if not payment_mode or payment_mode not in ['Cash', 'Online']:
        flash('Please select a payment mode!', 'danger')
        return redirect(url_for('order.list'))

    # Mark as paid
    order.is_paid = True
    order.paid_at = datetime.now(timezone.utc)
    order.status = 'Paid'
    db.session.commit()

    # Generate bill
    bill = Bill.query.filter_by(order_id=order.id).first()
    if not bill:
        total_items = order.total_amount
        gst = total_items * 0
        service_charge = total_items * 0
        grand_total = total_items + gst + service_charge

        bill = Bill(
            order_id=order.id,
            total_items=total_items,
            gst=gst,
            service_charge=service_charge,
            grand_total=grand_total,
            payment_mode=payment_mode  # ← SAVE PAYMENT MODE
        )
        db.session.add(bill)
        db.session.commit()

        # Finance entry
        from ..models.finance import FinanceTransaction, TransactionType
        inflow = FinanceTransaction(
            type=TransactionType.INFLOW,
            amount=grand_total,
            description=f'{payment_mode} payment for Order #{order.id}',
        )
        db.session.add(inflow)
        db.session.commit()

    flash(f'Payment via {payment_mode} successful! Bill generated.', 'success')
    return redirect(url_for('billing.view_invoice', id=bill.id))

@order_bp.route('/view/<int:id>')
@login_required
def view_order(id):
    order = Order.query.get_or_404(id)

    # Correct way to get bill
    bill = Bill.query.filter_by(order_id=order.id).first()

    if not bill:
        # Auto generate bill if not exists
        total_items = order.total_amount
        gst = total_items * 0
        service_charge = total_items * 0
        grand_total = total_items + gst + service_charge

        bill = Bill(
            order_id=order.id,
            total_items=total_items,
            gst=gst,
            service_charge=service_charge,
            grand_total=grand_total
        )
        db.session.add(bill)
        db.session.commit()

        # Add to finance
        from ..models.finance import FinanceTransaction, TransactionType
        inflow = FinanceTransaction(
            type=TransactionType.INFLOW,
            amount=grand_total,
            description=f'Auto bill for Order #{order.id}',
        )
        db.session.add(inflow)
        db.session.commit()

        flash(f'Bill automatically generated for Order #{order.id}', 'success')

    return redirect(url_for('billing.view_invoice', id=bill.id))
