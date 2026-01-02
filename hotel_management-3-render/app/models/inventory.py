from ..extensions import db
from enum import Enum

class InventoryCategory(Enum):
    TOOLS = 'TOOLS'
    UTENSILS = 'UTENSILS'
    APPLIANCES = 'APPLIANCES'
    FURNITURE = 'FURNITURE'
    OTHER = 'OTHER'
    GROCERY = 'GROCERY'

class InventoryStatus(Enum):
    USING = 'USING'
    UNUSED = 'UNUSED'
    BROKEN = 'BROKEN'

class PaymentMode(Enum):
    CASH = 'CASH'
    ONLINE = 'ONLINE'

class Inventory(db.Model):
    item_id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.Enum(InventoryCategory), nullable=False)
    quantity_with_unit = db.Column(db.String(50), nullable=False)
    status = db.Column(db.Enum(InventoryStatus), nullable=False, default=InventoryStatus.UNUSED)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    expenses = db.relationship('Expense', backref='inventory', lazy=True, cascade='all, delete-orphan')

class Expense(db.Model):
    expense_id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory.item_id'), nullable=False)
    added_quantity_with_unit = db.Column(db.String(50), nullable=False)
    payment_amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_mode = db.Column(db.Enum(PaymentMode), nullable=False, default=PaymentMode.CASH)
    date = db.Column(db.DateTime, default=db.func.current_timestamp())