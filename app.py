# app.py
from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Ticket
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this in production!

# Mail config (use environment variables for security in deployment)
app.config.update({
    'MAIL_SERVER': 'smtp.gmail.com',
    'MAIL_PORT': 587,
    'MAIL_USE_TLS': True,
    'MAIL_USERNAME': 'shahdhir08@gmail.com',
    'MAIL_PASSWORD': 'exua dznq vuxl imcs'  # Use app password, not your Gmail password
})
mail = Mail(app)

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Home route
@app.route('/')
def index():
    return redirect('/dashboard') if 'user_id' in session else redirect('/login')

# Register new user
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please login.', 'success')
        return redirect('/login')
    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            session['role'] = user.role
            flash('Login successful!', 'success')
            return redirect('/dashboard')
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect('/login')

# Dashboard (shows tickets based on role)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    query = Ticket.query
    if session['role'] != 'admin':
        query = query.filter_by(user_id=session['user_id'])
    tickets = query.order_by(Ticket.created_at.desc()).all()
    return render_template('dashboard.html', tickets=tickets)

# Create Ticket
@app.route('/create', methods=['GET', 'POST'])
def create_ticket():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        priority = request.form['priority']
        ticket = Ticket(title=title, description=description, priority=priority, user_id=session['user_id'])
        db.session.add(ticket)
        db.session.commit()

        # Send notification email
        user = User.query.get(session['user_id'])
        try:
            msg = Message(f"Ticket Created: {title}",
                          sender=app.config['MAIL_USERNAME'],
                          recipients=[user.email])
            msg.body = f"Hi {user.username},\n\nYour ticket '{title}' was submitted successfully.\nPriority: {priority}\n\nDescription:\n{description}"
            mail.send(msg)
        except Exception as e:
            print("Email Error:", e)

        flash('Ticket created successfully!', 'success')
        return redirect('/dashboard')
    return render_template('ticket_form.html')

# Edit Ticket
@app.route('/edit/<int:ticket_id>', methods=['GET', 'POST'])
def edit_ticket(ticket_id):
    ticket = Ticket.query.get(ticket_id)
    if request.method == 'POST':
        ticket.title = request.form['title']
        ticket.description = request.form['description']
        ticket.status = request.form['status']
        ticket.priority = request.form['priority']
        db.session.commit()
        flash('Ticket updated.', 'info')
        return redirect('/dashboard')
    return render_template('ticket_form.html', ticket=ticket)

# Delete Ticket
@app.route('/delete/<int:ticket_id>')
def delete_ticket(ticket_id):
    ticket = Ticket.query.get(ticket_id)
    db.session.delete(ticket)
    db.session.commit()
    flash('Ticket deleted.', 'warning')
    return redirect('/dashboard')

# User Profile
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login')
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)

# DB createimport os

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

