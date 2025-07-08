from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import login_required, current_user
from app.models import Room, Equipment, Booking, db

bp = Blueprint('staff', __name__, url_prefix='/staff')

@bp.route('/dashboard')
@login_required
def dashboard():
    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    rooms = Room.query.all()
    equipment = Equipment.query.all()
    return render_template('dashboard.html', bookings=bookings, rooms=rooms, equipment=equipment)

@bp.route('/mark_returned/<int:booking_id>', methods=['POST'])
@login_required
def mark_returned(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    # Only the user who made the booking can mark it returned
    if booking.user_id != current_user.id:
        abort(403)

    if booking.status == 'Approved' and not booking.returned:
        booking.status = 'Returned'
        booking.returned = False  # Still pending admin verification
        db.session.commit()
        flash("Return submitted for admin verification.", "info")
    else:
        flash("This booking can't be marked as returned.", "warning")

    return redirect(url_for('booking.dashboard'))  # or wherever the user is sent

