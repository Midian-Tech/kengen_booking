from datetime import datetime, timedelta
from flask import Blueprint, flash, redirect, render_template, abort, request, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
from app.models import Notice, Room, Equipment, Booking
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
    if request.method == 'POST':
        action = request.form.get('action')
        room_id = request.form.get('room_id')

        if action == 'add':
            name = request.form.get('name')
            capacity = request.form.get('capacity')
            new_room = Room(name=name, capacity=capacity, status='Available')
            db.session.add(new_room)
            db.session.commit()
            flash("Room added successfully", "success")

        elif action == 'update':
            room = Room.query.get(room_id)
            if room:
                room.name = request.form.get('name')
                room.capacity = request.form.get('capacity')
                room.status = request.form.get('status')
                db.session.commit()
                flash("Room updated successfully", "info")

        elif action == 'delete':
            room = Room.query.get(room_id)
            if room:
                db.session.delete(room)
                db.session.commit()
                flash("Room deleted successfully", "danger")

    rooms = Room.query.all()
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
    total = Booking.query.count()

    # Room stats
    room_stats = (
        db.session.query(Room.name, func.count(Booking.id))
        .join(Booking)
        .group_by(Room.name)
        .all()
    )
    room_stats = dict(room_stats)

    # Equipment stats
    equipment_stats = (
        db.session.query(Equipment.name, func.count(Booking.id))
        .join(Booking)
        .group_by(Equipment.name)
        .all()
    )
    equipment_stats = dict(equipment_stats)

    return render_template('reports.html',
                           total=total,
                           room_stats=room_stats,
                           equipment_stats=equipment_stats)

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
@bp.route('/notice', methods=['GET', 'POST'])
@login_required
def manage_notice():
    if current_user.role != 'admin':
        abort(403)

    latest_notice = Notice.query.order_by(Notice.created_at.desc()).first()

    if request.method == 'POST':
        new_notice = request.form.get('notice')
        if new_notice:
            db.session.add(Notice(message=new_notice))
            db.session.commit()
            flash("Notice updated!", "success")
            return redirect(url_for('admin.manage_notice'))

    return render_template('manage_notice.html', notice=latest_notice)
@bp.route('/bookings')
@login_required
def all_bookings():
    search_id = request.args.get('search_id', type=int)
    this_week = request.args.get('this_week') == '1'

    query = Booking.query

    if search_id:
        query = query.filter(Booking.id == search_id)

    if this_week:
        today = datetime.now()
        start_week = today - timedelta(days=today.weekday())  # Monday
        end_week = start_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
        query = query.filter(Booking.start_time >= start_week, Booking.start_time <= end_week)

    bookings = query.order_by(Booking.start_time.desc()).all()
    return render_template('admin/all_bookings.html', bookings=bookings)