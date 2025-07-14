from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user
from flask_mail import Message
from app.models import User
from app import db, login_manager



bp = Blueprint('auth', __name__, url_prefix='/auth')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and user.password == password:  # Consider using hashed passwords
            login_user(user)
            return redirect(url_for('admin.dashboard' if user.role == 'admin' else 'staff.dashboard'))

        flash("Invalid email or password", "danger")
        
    return render_template('login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']  # staff number input
        email = request.form['email']
        password = request.form['password']

        # Check if email or username already exists
        existing_email = User.query.filter_by(email=email).first()
        existing_username = User.query.filter_by(username=username).first()

        if existing_email:
            flash("Email already registered.", "danger")
            return redirect(url_for('auth.register'))
        
        if existing_username:
            flash("Staff number already in use.", "danger")
            return redirect(url_for('auth.register'))

        user = User(
            name=name,
            username=username,
            email=email,
            password=password,
            role='staff'
        )
        db.session.add(user)
        db.session.commit()

        flash("Account created. Please log in.", "success")
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()

        if user:
            # Generate token + send email logic here
            flash('A reset link has been sent to your email.', 'info')
        else:
            flash('If the email exists, a reset link will be sent.', 'warning')

        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')



@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
