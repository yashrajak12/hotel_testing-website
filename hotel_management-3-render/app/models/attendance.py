from ..extensions import db
from enum import Enum

class AttendanceStatus(Enum):
    PRESENT = 'Present'
    ABSENT = 'Absent'
    HALF_DAY = 'Half Day'

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum(AttendanceStatus), nullable=False)

