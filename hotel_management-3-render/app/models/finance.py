from ..extensions import db
from datetime import datetime

class TransactionType:
    INFLOW = 'Inflow'
    OUTFLOW = 'Outflow'

class FinanceTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)  # 'Inflow' or 'Outflow'
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    bill_id = db.Column(db.Integer, db.ForeignKey('bill.id'))  # Link to bill if inflow