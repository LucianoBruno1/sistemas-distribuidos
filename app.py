from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room, Namespace
from flask_sqlalchemy import SQLAlchemy
import pika
import os

app = Flask(__name__)
io = SocketIO(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'chat.db')
db = SQLAlchemy(app)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room = db.Column(db.String(50))
    name = db.Column(db.String(50))
    message = db.Column(db.String(500))

# Configuração RabbitMQ
# Configuração RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq', port=5672, heartbeat=600))
channel = connection.channel()
channel.queue_declare(queue='chat_messages')

@app.route("/")
def home():
    return render_template("chat.html")

class ChatNamespace(Namespace):
    def on_connect(self):
        pass

    def on_disconnect(self):
        pass

    def on_join(self, data):
        room = data['room']
        join_room(room)
        messages = Message.query.filter_by(room=room).all()
        emit('message', [{'name': msg.name, 'message': msg.message} for msg in messages], room=room)

    def on_leave(self, data):
        room = data['room']
        leave_room(room)

    def on_send_message(self, msg):
        room = msg.get('room', None)
        messages = Message.query.filter_by(room=room).all()
        emit('message', [{'name': msg.name, 'message': msg.message} for msg in messages], room=room)

        # Salva a mensagem no banco de dados
        with app.app_context():
            db.session.add(Message(room=room, name=msg['name'], message=msg['message']))
            db.session.commit()

        # Envia a mensagem para o RabbitMQ
        channel.basic_publish(exchange='', routing_key='chat_messages', body=str(msg))

# Registro do namespace
io.on_namespace(ChatNamespace('/chat'))

if __name__ == '__main__':
    # Criação das tabelas dentro do contexto da aplicação
    with app.app_context():
        db.create_all()

    io.run(app, host='0.0.0.0', port=5000, debug=True)