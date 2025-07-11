from flask import Blueprint, abort, current_app, make_response, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
import qrcode
import io
from weasyprint import HTML
import base64

from app.models import ConferenceBooking, Room, Equipment, User, db
from app.utils.email import send_email

bp = Blueprint('booking', __name__, url_prefix='/booking')


@bp.route('/book-conference', methods=['GET', 'POST'])
@login_required
def book_conference():
    if request.method == 'POST':
        booking = ConferenceBooking(
            function=request.form['function'],
            date_from=request.form['date_from'],
            date_to=request.form['date_to'],
            pax=request.form['pax'],
            room_id=request.form['room_id'],  # selected room
            equipment_id=request.form.get('equipment_id'),  # optional
            meals=','.join(request.form.getlist('meals')),
            cost_centre=request.form['cost_centre'],
            account_to_charge=request.form['account'],
            internal_order=request.form['internal_order'],
            network=request.form['network'],
            designation=request.form['designation'],
            area=request.form['area'],
            approval_date = request.form.get('approval_date'),
            user_id=current_user.id,
            approver_id=request.form['approver_id'],  # ✅ new: reference to User
            status='Pending'
        )
        db.session.add(booking)
        db.session.commit()
        flash('Booking submitted successfully. Awaiting approval.', 'success')
        return redirect(url_for('booking.my_bookings'))

    rooms = Room.query.all()
    equipment = Equipment.query.all()
    admins = User.query.filter_by(role='admin').all()  # ✅ pass admins to form
    return render_template('book_conference.html', rooms=rooms, equipment=equipment, admins=admins)


@bp.route('/my')
@login_required
def my_bookings():
    booking_id = request.args.get('booking_id', type=int)
    if booking_id:
        bookings = ConferenceBooking.query.filter_by(user_id=current_user.id, id=booking_id).all()
    else:
        bookings = ConferenceBooking.query.filter_by(user_id=current_user.id).all()

    return render_template('my_bookings.html', bookings=bookings)


@bp.route('/approvals')
@login_required
def view_approvals():
    bookings = ConferenceBooking.query.order_by(ConferenceBooking.created_at.desc()).all()
    return render_template('approve_bookings.html', bookings=bookings)


@bp.route('/approve/<int:booking_id>')
@login_required
def approve_booking(booking_id):
    booking = ConferenceBooking.query.get_or_404(booking_id)
    booking.status = 'Approved'
    booking.is_approved = True

    user = booking.user
    if user and user.email:
        send_email(
            subject="Booking Approved",
            recipients=[user.email],
            body=f"Hello {user.name},\n\nYour booking request (ID: {booking.id}) has been approved.",
            html=f"<p>Hello {user.name},</p><p>Your booking request (ID: <b>{booking.id}</b>) has been <b>approved</b>.</p>"
        )

    db.session.commit()
    flash('Booking approved.', 'success')
    return redirect(url_for('booking.view_approvals'))


@bp.route('/reject/<int:booking_id>')
@login_required
def reject_booking(booking_id):
    booking = ConferenceBooking.query.get_or_404(booking_id)
    booking.status = 'Rejected'
    booking.is_approved = False

    user = booking.user
    if user and user.email:
        send_email(
            subject="Booking Rejected",
            recipients=[user.email],
            body=f"Hello {user.name},\n\nUnfortunately, your booking request (ID: {booking.id}) has been rejected.",
            html=f"<p>Hello {user.name},</p><p>Your booking request (ID: <b>{booking.id}</b>) has been <b>rejected</b>.</p>"
        )

    db.session.commit()
    flash('Booking rejected.', 'danger')
    return redirect(url_for('booking.view_approvals'))


@bp.route('/print-ticket/<int:booking_id>')
@login_required
def print_ticket(booking_id):
    booking = ConferenceBooking.query.get_or_404(booking_id)
    if booking.status != 'Approved':
        abort(403)

    qr = qrcode.make(f"Booking ID: {booking.id}")
    qr_io = io.BytesIO()
    qr.save(qr_io, format='PNG')
    qr_data = base64.b64encode(qr_io.getvalue()).decode('utf-8')

    rendered = render_template('ticket_pdf.html', booking=booking, qr_code=qr_data)
    pdf = HTML(string=rendered).write_pdf()

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=booking_{booking.id}.pdf'
    return response
