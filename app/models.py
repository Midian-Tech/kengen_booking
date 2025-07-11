from flask_login import UserMixin
from datetime import datetime
from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin' or 'staff'

    # ✅ Remove redundant relationship declaration
    # bookings = db.relationship('ConferenceBooking', backref='user', lazy=True)  ❌ REMOVE


class Room(db.Model):
    __tablename__ = 'room'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    capacity = db.Column(db.Integer)
    status = db.Column(db.String(20), default="available")


class Equipment(db.Model):
    __tablename__ = 'equipment'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(100), nullable=False)  # e.g., "good", "dim", etc.

    def __repr__(self):
        return f"<Equipment {self.name}>"


class ConferenceBooking(db.Model):
    __tablename__ = 'conference_booking'

    id = db.Column(db.Integer, primary_key=True)

    function = db.Column(db.String(255))
    date_from = db.Column(db.DateTime)
    date_to = db.Column(db.DateTime)
    pax = db.Column(db.Integer)
    meals = db.Column(db.String(255))
    cost_centre = db.Column(db.String(100))
    account_to_charge = db.Column(db.String(100))
    internal_order = db.Column(db.String(100))
    network = db.Column(db.String(100))
    approver = db.Column(db.String(100))
    designation = db.Column(db.String(100))
    area = db.Column(db.String(100))
    approval_date = db.Column(db.DateTime)
    status = db.Column(db.String(50), default='Pending')
    returned = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    approver_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # ✅ New FK for approver
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=True)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='bookings_made')  # ✅ Explicit FK
    approver_user = db.relationship('User', foreign_keys=[approver_id], backref='bookings_to_approve')  # ✅ Explicit FK
    room = db.relationship('Room', backref='bookings')
    equipment = db.relationship('Equipment', backref='bookings')
    approver_user = db.relationship('User', foreign_keys=[approver_id])



class Notice(db.Model):
    __tablename__ = 'notice'

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
