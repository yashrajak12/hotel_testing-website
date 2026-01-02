from ..extensions import db
from datetime import datetime, timezone


class PaymentMode:
    CASH = 'Cash'
    ONLINE = 'Online'


class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False, unique=True)
    total_items = db.Column(db.Float, nullable=False)
    gst = db.Column(db.Float, nullable=False)
    service_charge = db.Column(db.Float, nullable=False)
    grand_total = db.Column(db.Float, nullable=False)
    generated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # NEW: Payment Mode
    payment_mode = db.Column(db.String(20), nullable=False)  # 'Cash' or 'Online'

    order = db.relationship('Order', backref=db.backref('bill', uselist=False))