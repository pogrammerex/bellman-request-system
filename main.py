from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from datetime import datetime
import os

app = Flask(__name__)

# Configure SQLite Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bellman_requests.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
socketio = SocketIO(app)

# Database Models
class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), default='Pending')

class FinishedRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room = db.Column(db.String(10), nullable=False)
    time_finished = db.Column(db.String(50), nullable=False)

# Uncomment this the first time to create the tables
#with app.app_context():
#    db.create_all()

@app.route('/')
def index():
    active_requests = Request.query.all()
    return render_template('index.html', requests=active_requests)

@app.route('/add', methods=['POST'])
def add_request():
    room_number = request.form.get('room_number')
    if room_number:
        new_request = Request(room=room_number)
        db.session.add(new_request)
        db.session.commit()
        # Notify clients about the new request
        socketio.emit('update_requests', {'room_number': room_number})  # Pass room_number as data
    return redirect(url_for('index'))

@app.route('/update/<int:request_id>/<status>', methods=['POST'])
def update_request(request_id, status):
    request_to_update = Request.query.get_or_404(request_id)
    request_to_update.status = status
    db.session.commit()
    # Notify clients about the updated request
    socketio.emit('update_requests', {'room_number': request_to_update.room})  # Pass room_number as data
    return redirect(url_for('index'))

@app.route('/finish/<int:request_id>', methods=['POST'])
def finish_request(request_id):
    request_to_finish = Request.query.get_or_404(request_id)
    finished_request = FinishedRequest(room=request_to_finish.room, time_finished=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    db.session.delete(request_to_finish)
    db.session.add(finished_request)
    db.session.commit()
    # Notify clients about the finished request
    socketio.emit('update_requests', {'room_number': request_to_finish.room})  # Pass room_number as data
    return redirect(url_for('index'))

@app.route('/finished')
def view_finished():
    finished_requests = FinishedRequest.query.all()
    return render_template('finished.html', finished_requests=finished_requests)

@app.route('/clear-finished', methods=['POST'])
def clear_finished():
    db.session.query(FinishedRequest).delete()
    db.session.commit()
    return redirect(url_for('view_finished'))

@socketio.on('connect')
def handle_connect():
    print("Client connected")


if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))


