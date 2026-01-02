from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from ..extensions import db
from ..models.employee import Employee
from ..models.attendance import Attendance, AttendanceStatus
from datetime import date, datetime, timedelta
from ..routes.decorators import role_required

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')

@attendance_bp.route('/list/<int:employee_id>', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Manager')
def list(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    attendances = Attendance.query.filter_by(employee_id=employee_id).order_by(Attendance.date.desc()).all()

    if request.method == 'POST':
        date_str = request.form.get('date')
        status_str = request.form.get('status')
        deduction = float(request.form.get('deduction', 0.0))

        try:
            attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            status = AttendanceStatus(status_str)
        except ValueError:
            flash('Invalid date or status!', 'danger')
            return redirect(url_for('attendance.list', employee_id=employee_id))

        existing = Attendance.query.filter_by(employee_id=employee_id, date=attendance_date).first()
        if existing:
            flash('Attendance already marked for this date!', 'warning')
            return redirect(url_for('attendance.list', employee_id=employee_id))

        attendance = Attendance(
            employee_id=employee_id,
            date=attendance_date,
            status=status
        )
        db.session.add(attendance)
        db.session.commit()
        flash('Attendance marked successfully!', 'success')
        return redirect(url_for('attendance.list', employee_id=employee_id))

    # Salary Calculation (Current Month)
    today = date.today()
    month_start = today.replace(day=1)
    month_end = (month_start.replace(month=month_start.month % 12 + 1, day=1) if month_start.month < 12 else month_start.replace(year=month_start.year + 1, month=1, day=1)) - timedelta(days=1)

    monthly_attendances = Attendance.query.filter_by(employee_id=employee_id)\
        .filter(Attendance.date.between(month_start, month_end)).all()

    present_days = sum(1 for a in monthly_attendances if a.status == AttendanceStatus.PRESENT)
    half_days = sum(1 for a in monthly_attendances if a.status == AttendanceStatus.HALF_DAY)
    absent_days = sum(1 for a in monthly_attendances if a.status == AttendanceStatus.ABSENT)

    days_worked = present_days + (half_days * 0.5)
    daily_salary = employee.salary / 30  # 30-day month assumption
    calculated_salary = days_worked * daily_salary

    return render_template(
        'attendance/list.html',
        employee=employee,
        attendances=attendances,
        today=today,
        calculated_salary=calculated_salary,
        present_days=present_days,
        half_days=half_days,
        absent_days=absent_days
    )