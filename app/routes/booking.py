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
    rooms = Room.query.all()
    equipment = Equipment.query.all()
    admins = User.query.filter_by(role='admin').all()

    if request.method == 'POST':
        room_id = request.form.get('room_id')
        equipment_id = request.form.get('equipment_id')
        date_from_str = request.form['date_from']
        date_to_str = request.form['date_to']
        date_from = datetime.strptime(date_from_str, "%Y-%m-%d").date()

        # 1. Prevent booking if date_from is in the past
        if date_from < datetime.utcnow().date():
            flash('Booking date cannot be in the past.', 'danger')
            return render_template('book_conference.html', rooms=rooms, equipment=equipment, admins=admins)

        # 2. Require at least room or equipment
        if not room_id and not equipment_id:
            flash('Please select at least a room or equipment.', 'warning')
            return render_template('book_conference.html', rooms=rooms, equipment=equipment, admins=admins)

        # 3. Check availability
        if room_id:
            room = Room.query.get(room_id)
            if room.status == 'Unavailable':
                flash(f"Room '{room.name}' is currently unavailable.", 'danger')
                return render_template('book_conference.html', rooms=rooms, equipment=equipment, admins=admins)
        else:
            room = None

        if equipment_id:
            item = Equipment.query.get(equipment_id)
            if item.quantity < 1:
                flash(f"Equipment '{item.name}' is out of stock.", 'danger')
                return render_template('book_conference.html', rooms=rooms, equipment=equipment, admins=admins)
        else:
            item = None

        # All checks passed, create booking
        booking = ConferenceBooking(
            function=request.form['function'],
            date_from=request.form['date_from'],
            date_to=request.form['date_to'],
            pax=request.form['pax'],
            room_id=room_id if room else None,
            equipment_id=equipment_id if item else None,
            meals=','.join(request.form.getlist('meals')),
            cost_centre=request.form['cost_centre'],
            account_to_charge=request.form['account'],
            internal_order=request.form['internal_order'],
            network=request.form['network'],
            designation=request.form['designation'],
            area=request.form['area'],
            approval_date=request.form.get('approval_date'),
            user_id=current_user.id,
            approver_id=request.form['approver_id'],
            status='Pending'
        )

        db.session.add(booking)
        db.session.commit()

        # Send email to approver
        admin = User.query.get(booking.approver_id)
        if admin and admin.email:
            send_email(
                subject="New Conference Booking Awaiting Approval",
                recipients=[admin.email],
                body=f"Dear {admin.name},\n\nA new conference booking (ID: {booking.id}) is awaiting your approval.\n\nPlease log in to review it.",
                html=f"""
                    <p>Dear {admin.name},</p>
                    <p>A new <strong>conference booking</strong> (ID: <strong>{booking.id}</strong>) is awaiting your approval.</p>
                    <p><a href="{url_for('admin.pending_bookings', _external=True)}">Click here</a> to review it.</p>
                """
            )

        flash('Booking submitted successfully. Awaiting approval.', 'success')
        return redirect(url_for('booking.my_bookings'))

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
