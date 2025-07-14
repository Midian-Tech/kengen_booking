from datetime import datetime, timedelta
from flask import Blueprint, flash, redirect, render_template, abort, request, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
from app.models import ConferenceBooking, Notice, Room, Equipment, User
from app import db
from app.utils.email import send_email
from datetime import datetime
from zoneinfo import ZoneInfo


bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        abort(403)

    bookings = ConferenceBooking.query.all()
    pending_bookings = ConferenceBooking.query.filter_by(status='Pending').order_by(ConferenceBooking.date_from).all()
    rooms = Room.query.all()
    equipment = Equipment.query.all()

    # Generate dynamic data for usage analytics
    room_labels = []
    booking_counts = []

    for room in rooms:
        count = ConferenceBooking.query.filter_by(room_id=room.id).count()
        room_labels.append(room.name)
        booking_counts.append(count)

    return render_template(
        'dashboard.html',
        bookings=bookings,
        pending_bookings=pending_bookings,
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

@bp.route('/approve/<int:booking_id>', methods=['POST'])
@login_required
def approve_booking(booking_id):
    if current_user.role != 'admin':
        abort(403)

    booking = ConferenceBooking.query.get_or_404(booking_id)

    if booking.status != 'Pending':
        flash('Booking is not pending approval.', 'warning')
        return redirect(url_for('admin.pending_bookings'))

    if booking.room:
        if booking.room.status == 'Unavailable':
            flash(f"Cannot approve booking: Room '{booking.room.name}' is currently unavailable.", 'danger')
            return redirect(url_for('admin.pending_bookings'))
        else:
            booking.room.status = 'Unavailable'

    elif booking.equipment:
        if booking.equipment.quantity < 1:
            flash(f"Cannot approve booking: Equipment '{booking.equipment.name}' is out of stock.", 'danger')
            return redirect(url_for('admin.pending_bookings'))
        else:
            booking.equipment.quantity -= 1

    booking.status = 'Approved'
    booking.approver_id = current_user.id
    booking.approval_date = datetime.now(ZoneInfo("Africa/Nairobi"))

    db.session.commit()

    # ✅ Send approval email
    user = booking.user
    if user and user.email:
        send_email(
            subject="Booking Approved",
            recipients=[user.email],
            body=f"Hello {user.name},\n\nYour booking (ID: {booking.id}) has been approved.",
            html=f"<p>Hello {user.name},</p><p>Your booking (ID: <b>{booking.id}</b>) has been <b>approved</b>.</p>"
        )

    flash(f'Booking #{booking.id} approved and resources updated.', 'success')
    return redirect(url_for('admin.pending_bookings'))

@bp.route('/reports')
@login_required
def reports():
    total = ConferenceBooking.query.count()

    room_stats = (
        db.session.query(Room.name, func.count(ConferenceBooking.id))
        .join(ConferenceBooking)
        .group_by(Room.name)
        .all()
    )
    room_stats = dict(room_stats)

    equipment_stats = (
        db.session.query(Equipment.name, func.count(ConferenceBooking.id))
        .join(ConferenceBooking)
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

    unreturned = ConferenceBooking.query.filter_by(status='Approved', returned=False).all()
    return render_template('verify_returns.html', bookings=unreturned)


@bp.route('/mark_returned/<int:booking_id>', methods=['POST'])
@login_required
def mark_returned(booking_id):
    if current_user.role != 'admin':
        abort(403)

    booking = ConferenceBooking.query.get_or_404(booking_id)

    if booking.status == 'Approved' and not booking.returned:
        booking.returned = True
        booking.status = 'Completed'

        if booking.room:
            booking.room.status = 'Available'

        if booking.equipment:
            booking.equipment.quantity += 1

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

    query = ConferenceBooking.query

    if search_id:
        query = query.filter(ConferenceBooking.id == search_id)

    if this_week:
        today = datetime.now()
        start_week = today - timedelta(days=today.weekday())
        end_week = start_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
        query = query.filter(ConferenceBooking.date_from >= start_week, ConferenceBooking.date_from <= end_week)

    bookings = query.order_by(ConferenceBooking.date_from.desc()).all()
    return render_template('admin/all_bookings.html', bookings=bookings)
@bp.route('/pending-bookings')
@login_required
def pending_bookings():
    if current_user.role != 'admin':
        abort(403)
    bookings = ConferenceBooking.query.filter_by(status='Pending').order_by(ConferenceBooking.date_from).all()
    return render_template('admin/pending_bookings.html', bookings=bookings)
@bp.route('/reject/<int:booking_id>', methods=['POST'])
@login_required
def reject_booking(booking_id):
    booking = ConferenceBooking.query.get_or_404(booking_id)

    if current_user.role != 'admin' or booking.approver_id != current_user.id:
        abort(403)

    booking.status = 'Rejected'
    db.session.commit()

    # ✅ Send rejection email
    user = booking.user
    if user and user.email:
        send_email(
            subject="Booking Rejected",
            recipients=[user.email],
            body=f"Hello {user.name},\n\nYour booking (ID: {booking.id}) has been rejected.",
            html=f"<p>Hello {user.name},</p><p>Your booking (ID: <b>{booking.id}</b>) has been <b>rejected</b>.</p>"
        )

    flash(f'Booking #{booking.id} has been rejected.', 'danger')
    return redirect(url_for('admin.pending_bookings'))

@bp.route('/history')
@login_required
def history():
    if current_user.role != 'admin':
        abort(403)

    approver_query = request.args.get('approver', '').strip()

    query = ConferenceBooking.query.join(User, ConferenceBooking.approver_id == User.id)

    query = query.filter(ConferenceBooking.approval_date.isnot(None))  # approved only

    if approver_query:
        query = query.filter(User.name.ilike(f"%{approver_query}%"))

    bookings = query.order_by(ConferenceBooking.approval_date.desc()).all()

    return render_template('admin/history.html', bookings=bookings)

