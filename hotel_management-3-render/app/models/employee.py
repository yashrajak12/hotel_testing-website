from ..extensions import db
from datetime import date
from enum import Enum


class EmployeeRole(Enum):
    MANAGER = 'Manager'
    CHEF = 'Chef'
    WAITER = 'Waiter'
    CASHIER = 'Cashier'
    HOUSEKEEPING = 'Housekeeping'


class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)  # NEW: Age
    phone = db.Column(db.String(15))
    address = db.Column(db.Text)
    aadhaar_no = db.Column(db.String(12), unique=True)  # NEW: Aadhaar Number
    salary = db.Column(db.Float, nullable=False)
    role = db.Column(db.Enum(EmployeeRole), nullable=False)
    hire_date = db.Column(db.Date, nullable=False)
    resign_date = db.Column(db.Date, nullable=True)  # ← Fixed here

    attendances = db.relationship('Attendance', backref='employee', lazy=True, cascade="all, delete-orphan")