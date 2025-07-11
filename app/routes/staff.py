from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import login_required, current_user
from app.models import Notice, Room, Equipment, ConferenceBooking, db

bp = Blueprint('staff', __name__, url_prefix='/staff')

@bp.route('/dashboard')
@login_required
def dashboard():
    latest_notice = Notice.query.order_by(Notice.created_at.desc()).first()
    bookings = ConferenceBooking.query.filter_by(user_id=current_user.id).all()
    rooms = Room.query.all()
    equipment = Equipment.query.all()

    # Add room labels and booking counts
    room_labels = []
    booking_counts = []

    for room in rooms:
        room_labels.append(room.name)
        count = ConferenceBooking.query.filter_by(user_id=current_user.id, room_id=room.id).count()
        booking_counts.append(count)

    return render_template(
        'dashboard.html',
        bookings=bookings,
        rooms=rooms,
        equipment=equipment,
        notice=latest_notice,
        room_labels=room_labels,
        booking_counts=booking_counts
    )


@bp.route('/mark_returned/<int:booking_id>', methods=['POST'])
@login_required
def mark_returned(booking_id):
    booking = ConferenceBooking.query.get_or_404(booking_id)

    # Only the user who made the booking can mark it returned
    if booking.user_id != current_user.id:
        abort(403)

    if booking.status == 'Approved' and not booking.returned:
        booking.status = 'Returned'
        booking.returned = False  # Indicates it still needs admin verification
        db.session.commit()
        flash("Return submitted for admin verification.", "info")
    else:
        flash("This booking can't be marked as returned.", "warning")

    return redirect(url_for('staff.dashboard'))  # Make sure the route exists
