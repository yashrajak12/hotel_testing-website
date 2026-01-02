from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file
from flask_login import login_required
from app.extensions import db
from app.models.billing import Bill
from app.models.order import Order
from app.models.finance import FinanceTransaction, TransactionType
from datetime import datetime, date, timezone
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from ..routes.decorators import role_required

billing_bp = Blueprint('billing', __name__, url_prefix='/billing')


from datetime import datetime, date

@billing_bp.route('/')
@login_required
@role_required('Admin', 'Manager', 'Cashier')
def list():
    filter_date_str = request.args.get('date')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    query = Bill.query

    if filter_date_str:
        try:
            filter_date = datetime.strptime(filter_date_str, '%Y-%m-%d').date()
            query = query.filter(db.func.date(Bill.generated_at) == filter_date)
        except:
            flash('Invalid date format!', 'danger')
    elif start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            query = query.filter(db.func.date(Bill.generated_at).between(start_date, end_date))
        except:
            flash('Invalid date range!', 'danger')
    else:
        today = date.today()
        query = query.filter(db.func.date(Bill.generated_at) == today)

    # Ascending order (oldest first)
    bills = query.order_by(Bill.generated_at.asc()).all()

    # Add day-wise sequential number
    for index, bill in enumerate(bills, start=1):
        bill.day_sequence = index  # Temporary attribute

    return render_template('billing/list.html', bills=bills)


@billing_bp.route('/view_invoice/<int:id>')
@login_required
@role_required('Admin', 'Manager', 'Cashier')
def view_invoice(id):
    bill = Bill.query.get_or_404(id)
    return render_template('billing/invoice.html', bill=bill)


@billing_bp.route('/download_pdf/<int:id>')
@login_required
@role_required('Admin', 'Manager', 'Cashier')
def download_pdf(id):
    bill = Bill.query.get_or_404(id)
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, height - 50, "Hotel Management Invoice")

    p.setFont("Helvetica", 12)
    p.drawString(50, height - 100, f"Invoice ID: #{bill.id}")
    p.drawString(50, height - 120, f"Order ID: #{bill.order_id}")
    p.drawString(50, height - 140, f"Generated: {bill.generated_at.strftime('%Y-%m-%d %H:%M')}")
    p.drawString(50, height - 160, f"Payment Mode: {bill.payment_mode}")

    p.drawString(50, height - 200, "Items Total:")
    p.drawString(400, height - 200, f"₹{bill.total_items}")

    p.drawString(50, height - 220, "GST (18%):")
    p.drawString(400, height - 220, f"₹{bill.gst}")

    p.drawString(50, height - 240, "Service Charge (5%):")
    p.drawString(400, height - 240, f"₹{bill.service_charge}")

    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 280, "Grand Total:")
    p.drawString(400, height - 280, f"₹{bill.grand_total}")

    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"invoice_{bill.id}.pdf", mimetype='application/pdf')