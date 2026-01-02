# Update app/models/order.py - Add edit_count field
from ..extensions import db
from datetime import datetime

class OrderStatus:
    PENDING = 'Pending'
    PREPARING = 'Preparing'
    READY = 'Ready'
    SERVED = 'Served'
    PAID = 'Paid'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_type = db.Column(db.String(20), nullable=False)
    table_number = db.Column(db.String(10))
    customer_name = db.Column(db.String(100))
    status = db.Column(db.String(20), default=OrderStatus.PENDING)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, default=0.0)
    edit_count = db.Column(db.Integer, default=0)

    # NEW: Payment Status
    is_paid = db.Column(db.Boolean, default=False)
    paid_at = db.Column(db.DateTime, nullable=True)

    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_time = db.Column(db.Float, nullable=False)
    added_after_edit = db.Column(db.Integer, default=0)  # 0 for original, n for added during nth edit

    menu_item = db.relationship('MenuItem')