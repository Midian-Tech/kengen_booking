from flask import Blueprint, flash, redirect, render_template, abort, request, url_for
from flask_login import login_required, current_user
from app.models import Room, Equipment, Booking
from app import db

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        abort(403)

    bookings = Booking.query.all()
    pending_bookings = Booking.query.filter_by(status='Pending').order_by(Booking.start_time).all()
    rooms = Room.query.all()
    equipment = Equipment.query.all()

    # Generate dynamic data for usage analytics
    room_labels = []
    booking_counts = []

    for room in rooms:
        count = Booking.query.filter_by(room_id=room.id).count()
        room_labels.append(room.name)
        booking_counts.append(count)

    return render_template(
        'dashboard.html',
        bookings=bookings,
        pending_bookings=pending_bookings,  # <-- now passed
        rooms=rooms,
        equipment=equipment,
        room_labels=room_labels,
        booking_counts=booking_counts
    )

@bp.route('/manage-equipment', methods=['GET', 'POST'])
@login_required
def manage_equipment():
    if current_user.role != 'admin':
        abort(403)

    equipment = Equipment.query.all()
    return render_template('manage_equipment.html', equipment=equipment)


@bp.route('/add_equipment', methods=['POST'])
@login_required
def add_equipment():
    if current_user.role != 'admin':
        abort(403)

    name = request.form['name']
    quantity = int(request.form['quantity'])
    status = request.form.get('status', 'good')

    new_item = Equipment(name=name, quantity=quantity, status=status)
    db.session.add(new_item)
    db.session.commit()
    flash("Equipment added successfully.", "success")
    return redirect(url_for('admin.manage_equipment'))


@bp.route('/edit_equipment/<int:id>', methods=['POST'])
@login_required
def edit_equipment(id):
    if current_user.role != 'admin':
        abort(403)

    equipment = Equipment.query.get_or_404(id)
    equipment.name = request.form['name']
    equipment.quantity = int(request.form['quantity'])
    equipment.status = request.form['status']
    db.session.commit()
    flash("Equipment updated successfully.", "success")
    return redirect(url_for('admin.manage_equipment'))


@bp.route('/delete_equipment/<int:id>', methods=['POST'])
@login_required
def delete_equipment(id):
    if current_user.role != 'admin':
        abort(403)

    equipment = Equipment.query.get_or_404(id)
    db.session.delete(equipment)
    db.session.commit()
    flash("Equipment deleted successfully.", "info")
    return redirect(url_for('admin.manage_equipment'))


@bp.route('/manage-rooms', methods=['GET', 'POST'])
@login_required
def manage_rooms():
    if current_user.role != 'admin':
        abort(403)

    rooms = Room.query.all()

    if request.method == 'POST':
        room_id = request.form['room_id']
        status = request.form['status']
        room = Room.query.get_or_404(room_id)
        room.status = status
        db.session.commit()
        flash("Room status updated.", "success")
        return redirect(url_for('admin.manage_rooms'))

    return render_template('manage_rooms.html', rooms=rooms)


@bp.route('/approve-bookings', methods=['GET', 'POST'])
@login_required
def approve_bookings():
    if current_user.role != 'admin':
        abort(403)

    pending = Booking.query.filter_by(status='Pending').all()

    if request.method == 'POST':
        booking_id = request.form['booking_id']
        action = request.form['action']
        booking = Booking.query.get_or_404(booking_id)

        if action == 'approve':
          booking.status = 'Approved'
          booking.returned = False  # Means: still ongoing, not yet returned

        elif action == 'reject':
            booking.status = 'Rejected'
        db.session.commit()
        flash(f"Booking has been {booking.status.lower()}.", "info")
        return redirect(url_for('admin.approve_bookings'))

    return render_template('approve_bookings.html', bookings=pending)





@bp.route('/reports')
@login_required
def reports():
    if current_user.role != 'admin':
        abort(403)

    bookings = Booking.query.all()
    rooms = Room.query.all()

    room_stats = {room.name: 0 for room in rooms}
    for b in bookings:
        if b.room:
            room_stats[b.room.name] += 1

    total_bookings = len(bookings)
    return render_template('admin/reports.html', total=total_bookings, room_stats=room_stats)
@bp.route('/unreturned')
@login_required
def unreturned_bookings():
    if current_user.role != 'admin':
        abort(403)

    # Get all approved but not yet returned
    unreturned = Booking.query.filter_by(status='Approved', returned=False).all()
    return render_template('verify_returns.html', bookings=unreturned)
@bp.route('/mark_returned/<int:booking_id>', methods=['POST'])
@login_required
def mark_returned(booking_id):
    if current_user.role != 'admin':
        abort(403)

    booking = Booking.query.get_or_404(booking_id)

    if booking.status == 'Approved' and not booking.returned:
        booking.returned = True
        booking.status = 'Completed'

        if booking.room:
            booking.room.status = 'Available'

        if booking.equipment:
            booking.equipment.quantity += 1  # Or set to "Available"

        db.session.commit()
        flash("Booking marked as returned and resources updated.", "success")
    else:
        flash("Invalid return marking.", "warning")

    return redirect(url_for('admin.unreturned_bookings'))
