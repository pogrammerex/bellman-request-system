import eventlet
eventlet.monkey_patch()
from flask import Flask, render_template, request, redirect, url_for, session
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'
bcrypt = Bcrypt(app)
socketio = SocketIO(app)

# Fix for Heroku's postgres:// to postgresql://
uri = os.environ.get('DATABASE_URL')  # Get the database URL from Heroku
if uri and uri.startswith('postgres://'):
    uri = uri.replace('postgres://', 'postgresql://', 1)

# Configure PostgreSQL using Heroku's environment variable or fallback for local testing
app.config['SQLALCHEMY_DATABASE_URI'] = uri or 'sqlite:///bellman_requests.db'  # Fallback to SQLite for local testing
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)

# Set the login page as the default for unauthorized access
login_manager.login_view = 'login'  # 'login' refers to the login route

# User Model with roles
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # Operator, Bellman, BellmanAdmin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes for login and logout
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            error = "Username or password is not correct"
            return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Page where only Operators and BellmanAdmins can add requests
@app.route('/')
@login_required
def index():
    if current_user.role in ['Operator', 'BellmanAdmin']:
        active_requests = Request.query.all()
        return render_template('index.html', requests=active_requests)  # Operators and BellmanAdmins can add/view requests
    elif current_user.role == 'Bellman':
        active_requests = Request.query.all()
        return render_template('view_only.html', requests=active_requests)  # Bellman can only view requests
    else:
        return 'Unauthorized', 403

# Database Models
class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), default='Pending')

class FinishedRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room = db.Column(db.String(10), nullable=False)
    time_finished = db.Column(db.String(50), nullable=False)


@app.route('/add', methods=['POST'])
@login_required  # This ensures that the user is logged in
def add_request():
    # Only Operators and BellmanAdmins can add requests
    if current_user.role in ['Operator', 'BellmanAdmin']:
        room_number = request.form.get('room_number')
        if room_number:
            new_request = Request(room=room_number)
            db.session.add(new_request)
            db.session.commit()
            # Notify clients about the new request
            socketio.emit('update_requests', {'room_number': room_number})
        return redirect(url_for('index'))
    else:
        return 'Unauthorized', 403


@app.route('/update/<int:request_id>/<status>', methods=['POST'])
@login_required
def update_request(request_id, status):
    if current_user.role in ['Operator', 'BellmanAdmin', 'Bellman']:  # Only Operators and BellmanAdmins can update
        request_to_update = Request.query.get_or_404(request_id)
        request_to_update.status = status
        db.session.commit()
        # Notify clients about the updated request
        socketio.emit('update_requests', {'room_number': request_to_update.room})
        return redirect(url_for('index'))
    else:
        return 'Unauthorized', 403


@app.route('/finish/<int:request_id>', methods=['POST'])
@login_required
def finish_request(request_id):
    if current_user.role in ['Operator', 'BellmanAdmin', 'Bellman']:  # Only Operators and BellmanAdmins can mark requests as finished
        request_to_finish = Request.query.get_or_404(request_id)
        finished_request = FinishedRequest(room=request_to_finish.room, time_finished=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        db.session.delete(request_to_finish)
        db.session.add(finished_request)
        db.session.commit()
        # Notify clients about the finished request
        socketio.emit('update_requests', {'room_number': request_to_finish.room})
        return redirect(url_for('index'))
    else:
        return 'Unauthorized', 403

@app.route('/finished')
def view_finished():
    finished_requests = FinishedRequest.query.all()
    return render_template('finished.html', finished_requests=finished_requests)

@app.route('/clear-finished', methods=['POST'])
@login_required
def clear_finished():
    if current_user.role == 'BellmanAdmin':  # Only BellmanAdmins can clear finished requests
        if request.form.get('password'):
            admin = User.query.filter_by(username=current_user.username).first()
            if bcrypt.check_password_hash(admin.password, request.form['password']):  # Check password
                db.session.query(FinishedRequest).delete()  # Clear finished requests
                db.session.commit()
                return redirect(url_for('view_finished'))
            else:
                return 'Password Incorrect', 401
        return render_template('clear_confirm.html')  # Prompt for password
    else:
        return 'Unauthorized', 403

@socketio.on('connect')
def handle_connect():
    print("Client connected")

# Function to create or update users in the app context
# Function to create or update users in the app context
def create_or_update_users():
    with app.app_context():
        db.create_all()

        # Admin user
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            # Check if another user with the new username 'majed' exists
            existing_user = User.query.filter_by(username='majed').first()
            
            if existing_user and existing_user.id != admin_user.id:
                print("Username 'majed' is already taken by another user!")
            else:
                # Update admin's username or password if needed
                admin_user.username = 'majed'  # Change this if needed
                admin_user.password = bcrypt.generate_password_hash('11223344').decode('utf-8')  # Change this if needed
                db.session.commit()
                print(f"Admin user updated to: {admin_user.username}")
        else:
                # Create the admin user
                hashed_pw = bcrypt.generate_password_hash('11223344').decode('utf-8')
                admin_user = User(username='admin', password=hashed_pw, role='BellmanAdmin')
                db.session.add(admin_user)
                db.session.commit()
                print("Admin user created!")

            # Operator user
        operator_user = User.query.filter_by(username='operator').first()
        if operator_user:
            print(f"Operator user already exists: {operator_user.username}")
        else:
                hashed_pw = bcrypt.generate_password_hash('123456789').decode('utf-8')
                operator_user = User(username='operator', password=hashed_pw, role='Operator')
                db.session.add(operator_user)
                print("Operator user created!")

            # Bellman user
        bellman_user = User.query.filter_by(username='bellman').first()
        if bellman_user:
                print(f"Bellman user already exists: {bellman_user.username}")
        else:
                hashed_pw = bcrypt.generate_password_hash('123456').decode('utf-8')
                bellman_user = User(username='bellman', password=hashed_pw, role='Bellman')
                db.session.add(bellman_user)
                print("Bellman user created!")

            # Commit the changes to the database
        db.session.commit()


if __name__ == "__main__":
    create_or_update_users()


    socketio.run(app, debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

