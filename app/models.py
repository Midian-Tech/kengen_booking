from flask_login import UserMixin
from datetime import datetime
from app.extensions import db  # ✅ Assumes SQLAlchemy is initialized here


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin' or 'staff'

    # Reverse relationship (optional, already established via backref)
    # bookings = db.relationship('Booking', back_populates='user')


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


class Booking(db.Model):
    __tablename__ = 'booking'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=True)

    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    status = db.Column(db.String(20), default='Pending')  # e.g. 'Pending', 'Approved', etc.
    returned = db.Column(db.Boolean, default=False)
    user_signed = db.Column(db.Boolean, default=False)

    # Relationships
    user = db.relationship('User', backref=db.backref('bookings', lazy=True))
    room = db.relationship('Room', backref=db.backref('bookings', lazy=True))
    equipment = db.relationship('Equipment', backref=db.backref('bookings', lazy=True))


class Notice(db.Model):
    __tablename__ = 'notice'

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
