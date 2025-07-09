from flask import Blueprint, abort, current_app, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
import qrcode
import io
from weasyprint import HTML
import base64
from app.models import Booking, Room, Equipment, db
from app.utils.email import send_email
from flask import render_template, send_file
import io
from reportlab.pdfgen import canvas 
bp = Blueprint('booking', __name__, url_prefix='/booking')

@bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_booking():
    rooms = Room.query.all()
    equipment = Equipment.query.all()

    if request.method == 'POST':
        room_id = request.form.get('room') or None
        equipment_id = request.form.get('equipment') or None
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')

        room = Room.query.get(room_id) if room_id else None
        equip = Equipment.query.get(equipment_id) if equipment_id else None

        # Validate: at least one (room or equipment) must be selected
        if not room and not equip:
            flash("Please select at least a room or equipment.", "danger")
            return redirect(url_for('booking.create_booking'))

        if room and room.status != 'Available':
            flash("Selected room is not available.", "danger")
            return redirect(url_for('booking.create_booking'))

        if equip and equip.quantity <= 0:
            flash("Selected equipment is not available.", "danger")
            return redirect(url_for('booking.create_booking'))

        # Save the booking
        booking = Booking(
            user_id=current_user.id,
            room_id=room.id if room else None,
            equipment_id=equip.id if equip else None,
            start_time=start_time,
            end_time=end_time,
            status='Pending'
        )
        db.session.add(booking)
        db.session.commit()
        admin_email = current_app.config.get('ADMIN_EMAIL')
        if admin_email:
            subject = "New Booking Request Pending Approval"
            body = f"""
            Hello Admin,

            A new booking has been submitted by {current_user.name}.

            Details:
            Room: {room.name if room else '—'}
            Equipment: {equip.name if equip else '—'}
            Start: {start_time}
            End: {end_time}

            Please log in to the system to approve or reject this booking.

            Regards,
            Booking System
            """
            send_email(subject, [admin_email], body)

        flash("Booking request submitted!", "success")
        return redirect(url_for('booking.create_booking'))

    return render_template('booking/create_booking.html', rooms=rooms, equipment=equipment)


@bp.route('/my')
@login_required
def my_bookings():
    booking_id = request.args.get('booking_id', type=int)

    if booking_id:
        # Filter by booking ID and current user
        bookings = Booking.query.filter_by(user_id=current_user.id, id=booking_id).all()
    else:
        # Show all bookings for the user
        bookings = Booking.query.filter_by(user_id=current_user.id).all()

    return render_template('my_bookings.html', bookings=bookings)



@bp.route('/approve/<int:booking_id>')
@login_required
def approve_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    booking.status = 'Approved'

    if booking.room:
        booking.room.status = 'Booked'

    if booking.equipment and booking.equipment.quantity > 0:
        booking.equipment.quantity -= 1

    # Fetch user info
    user = booking.user
    if user and user.email:
        send_email(
            subject="Booking Approved",
            recipients=[user.email],
            body=f"Hello {user.name},\n\nYour booking request (ID: {booking.id}) has been approved.\n\nThanks.",
            html=f"<p>Hello {user.name},</p><p>Your booking request (ID: <b>{booking.id}</b>) has been <b>approved</b>.</p>"
        )

    db.session.commit()
    flash('Booking approved.', 'success')
    return redirect(url_for('booking.view_approvals'))


@bp.route('/reject/<int:booking_id>')
@login_required
def reject_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    booking.status = 'Rejected'

    # Fetch user info
    user = booking.user
    if user and user.email:
        send_email(
            subject="Booking Rejected",
            recipients=[user.email],
            body=f"Hello {user.name},\n\nUnfortunately, your booking request (ID: {booking.id}) has been rejected.\n\nRegards.",
            html=f"<p>Hello {user.name},</p><p>Your booking request (ID: <b>{booking.id}</b>) has been <b>rejected</b>.</p>"
        )

    db.session.commit()
    flash('Booking rejected.', 'danger')
    return redirect(url_for('booking.view_approvals'))


@bp.route('/return/<int:booking_id>')
@login_required
def return_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    booking.returned = True

    if booking.room:
        booking.room.status = 'Available'

    if booking.equipment:
        booking.equipment.quantity += 1

    db.session.commit()
    flash('Booking marked as returned.', 'info')
    return redirect(url_for('booking.my_bookings'))


@bp.route('/approvals')
@login_required
def view_approvals():
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template('approve_bookings.html', bookings=bookings)
@bp.route('/ticket/<int:booking_id>')
@login_required
def generate_ticket(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != current_user.id and current_user.role != 'admin':
        abort(403)

    ticket_code = f"TKT-{booking.id:06}"

    # Generate QR Code
    qr = qrcode.make(f"Booking ID: {booking.id}, Code: {ticket_code}")
    qr_buffer = io.BytesIO()
    qr.save(qr_buffer)
    qr_buffer.seek(0)
    qr_base64 = base64.b64encode(qr_buffer.read()).decode('utf-8')

    # Render HTML with QR code embedded as base64 image
    html_out = render_template('ticket_template.html', booking=booking, ticket_code=ticket_code, qr_image=qr_base64)

    # Generate PDF
    pdf_buffer = HTML(string=html_out).write_pdf()

    return send_file(
        io.BytesIO(pdf_buffer),
        mimetype='application/pdf',
        download_name=f"ticket_{booking.id}.pdf",
        as_attachment=True
    )