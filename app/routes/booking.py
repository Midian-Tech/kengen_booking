from flask import Blueprint, abort, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from app.models import Booking, Room, Equipment, db

bp = Blueprint('booking', __name__, url_prefix='/booking')

@bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_booking():
    rooms = Room.query.all()
    equipment = Equipment.query.all()

    if request.method == 'POST':
        room_id = request.form.get('room')
        equipment_id = request.form.get('equipment') or None
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')

        room = Room.query.get(room_id)
        if room.status != 'Available':
            flash("Selected room is not available.", "danger")
            return redirect(url_for('booking.create_booking'))

        if equipment_id:
            equip = Equipment.query.get(equipment_id)
            if equip.quantity <= 0:
                flash("Selected equipment is not available.", "danger")
                return redirect(url_for('booking.create_booking'))

        # Save the booking
        booking = Booking(
            user_id=current_user.id,
            room_id=room_id,
            equipment_id=equipment_id,
            start_time=start_time,
            end_time=end_time,
            status='Pending'
        )
        db.session.add(booking)
        db.session.commit()
        flash("Booking request submitted!", "success")
        return redirect(url_for('booking.create_booking'))

    return render_template('booking/create_booking.html', rooms=rooms, equipment=equipment)


@bp.route('/my')
@login_required
def my_bookings():
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

    db.session.commit()
    flash('Booking approved.', 'success')
    return redirect(url_for('booking.view_approvals'))

@bp.route('/reject/<int:booking_id>')
@login_required
def reject_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    booking.status = 'Rejected'
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
