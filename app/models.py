# app/models.py

from flask_login import UserMixin
from datetime import datetime
from app.extensions import db  # ✅ Fixed import

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin' or 'staff'

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    capacity = db.Column(db.Integer)
    status = db.Column(db.String(20), default="available")

class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(100), nullable=False)  # e.g., "good", "dim", etc.

    def __repr__(self):
        return f"<Equipment {self.name}>"



class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Pending')
    returned = db.Column(db.Boolean, default=False)
    user_signed = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref='bookings')
    room = db.relationship('Room', backref='bookings')
    equipment = db.relationship('Equipment', backref='bookings')
