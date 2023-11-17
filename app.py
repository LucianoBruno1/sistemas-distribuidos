from flask import Flask, render_template
from flask_socketio import SocketIO, emit, send
import pika

app = Flask(__name__)
io = SocketIO(app)

messages = []

# AQUI EU CONECTO COM O RABBITMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='chat_messages')

def consume_messages():
    # AQUI EU CONSUMO AS MENSAGENS ENVIADAS PRO RABBITMQ E ENVIO PRA TODOS OS USUARIOS
    for method_frame, properties, body in channel.consume('chat_messages', auto_ack=True):
        if body:
            message = body.decode('utf-8')
            io.emit('getMessage', message)

            # Adicionar a mensagem à lista
            messages.append(message)

@io.on('sendMessage')
def send_message_handler(msg):
    # Garantir que a mensagem contenha as propriedades 'name' e 'message'
    if 'name' in msg and 'message' in msg:
        # Adicionar o nome do remetente à mensagem antes de enviar para o RabbitMQ
        message = f"{msg['name']}: {msg['message']}"
        print('Mensagem enviada para o RabbitMQ:', message)  # AQUI EU USEI PRA DEBUGAR E VER A MENSAGEM QUE FOI ENVIADA PRO RABBIT
        channel.basic_publish(exchange='', routing_key='chat_messages', body=message)


@io.on('connect')
def handle_connect():
    io.start_background_task(consume_messages)

@app.route("/")
def home():
    return render_template("chat.html")

if __name__ == '__main__':
    io.run(app, debug=True)
