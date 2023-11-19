from flask import Flask, render_template
from flask_socketio import SocketIO, emit, send, join_room, leave_room

app = Flask(__name__)
io = SocketIO(app)

rooms = {}  # Dicionário para mapear salas e mensagens

@app.route("/")
def home():
    return render_template("chat.html")

@io.on('sendMessage')
def send_message_handler(msg):
    room = msg.get('room', None)
    messages = rooms.get(room, [])  # Obter mensagens da sala
    messages.append(msg)
    rooms[room] = messages
    emit('getMessage', msg, broadcast=True, room=room)

@io.on('join')
def join_handler(data):
    room = data['room']
    join_room(room)
    emit('message', rooms.get(room, []), room=room)

@io.on('leave')
def leave_handler(data):
    room = data['room']
    leave_room(room)

if __name__ == '__main__':
    io.run(app, debug=True)
