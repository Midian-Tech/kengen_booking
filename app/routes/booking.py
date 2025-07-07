from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Equipment, Room, Booking, db
from datetime import datetime

bp = Blueprint('booking', __name__, url_prefix='/booking')  # ✅ Add this line

@bp.route('/book', methods=['GET', 'POST']) # type: ignore
@login_required
def create_booking():
    if request.method == 'POST':
        room_id = request.form.get('room_id')
        equipment_id = request.form.get('equipment_id')
        start_time = datetime.strptime(request.form.get('start_time'), '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(request.form.get('end_time'), '%Y-%m-%dT%H:%M')

        # ✅ Check for double booking
        overlapping = Booking.query.filter(
            Booking.room_id == room_id,
            Booking.status == 'Approved',
            Booking.start_time < end_time,
            Booking.end_time > start_time
        ).first()
        if overlapping:
            flash("Room already booked for that time slot.", "danger")
            return redirect(url_for('booking.create_booking'))

        # ✅ Equipment availability check
        equipment = Equipment.query.get(equipment_id)
        if not equipment or equipment.quantity < 1:
            flash("Equipment not available.", "danger")
            return redirect(url_for('booking.create_booking'))

        # ✅ Reduce equipment count
        equipment.quantity -= 1
        db.session.add(equipment)

        # ✅ Create booking
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

        flash("Booking request submitted.", "success")
        return redirect(url_for('dashboard'))

    # On GET request, show the booking form
    rooms = Room.query.all()
    equipment_list = Equipment.query.all()
    return render_template('booking/create_booking.html', rooms=rooms, equipment=equipment_list)

