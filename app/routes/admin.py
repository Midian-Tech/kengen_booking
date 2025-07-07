from flask import Blueprint, flash, redirect, render_template, abort, request, url_for
from flask_login import login_required, current_user
from app.models import Room, Equipment, Booking
from app import db  # make sure this is imported

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/dashboard')
@login_required
def dashboard():
    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    rooms = Room.query.all()
    equipment = Equipment.query.all()
    return render_template('dashboard.html', bookings=bookings, rooms=rooms, equipment=equipment)


@bp.route('/manage-equipment', methods=['GET', 'POST'])
@login_required
def manage_equipment():
    if current_user.role != 'admin':
        abort(403)

    equipment = Equipment.query.all()

    if request.method == 'POST':
        item_id = request.form['item_id']
        available = True if request.form.get('available') == 'on' else False
        item = Equipment.query.get(item_id)
        item.available = available
        db.session.commit()
        flash("Equipment availability updated.", "success")
        return redirect(url_for('admin.manage_equipment'))

    return render_template('manage_equipment.html', equipment=equipment)


@bp.route('/manage-rooms', methods=['GET', 'POST'])
@login_required
def manage_rooms():
    if current_user.role != 'admin':
        abort(403)

    rooms = Room.query.all()

    if request.method == 'POST':
        room_id = request.form['room_id']
        status = request.form['status']
        room = Room.query.get(room_id)
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
        booking = Booking.query.get(booking_id)
        booking.status = 'Approved' if action == 'approve' else 'Rejected'
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

    # Count bookings per room
    room_stats = {room.name: 0 for room in rooms}
    for b in bookings:
        room_stats[b.room.name] += 1

    total_bookings = len(bookings)

    return render_template('admin/reports.html', total=total_bookings, room_stats=room_stats)
@bp.route('/verify_return/<int:booking_id>', methods=['POST'])
@login_required
def verify_return(booking_id):
    if current_user.role != 'admin':
        abort(403)

    booking = Booking.query.get_or_404(booking_id)
    if booking.returned:
        equipment = Equipment.query.get(booking.equipment_id)
        if equipment:
            equipment.quantity += 1

        booking.status = 'Completed'
        booking.user_signed = True
        db.session.commit()
        flash("Return verified and equipment restocked.", "success")

    return redirect(url_for('admin.approve_bookings'))
@bp.route('/add_equipment', methods=['POST'])
@login_required
def add_equipment():
    if current_user.role != 'admin':
        abort(403)

    name = request.form['name']
    quantity = int(request.form['quantity'])
    new_item = Equipment(name=name, quantity=quantity)
    db.session.add(new_item)
    db.session.commit()
    flash("Equipment added successfully", "success")
    return redirect(url_for('admin.manage_equipment'))
