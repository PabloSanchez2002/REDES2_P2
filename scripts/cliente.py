import os
import sys
import uuid
import pika
import time

ERROR = 0
OK = 1
REGISTERED = 2

def cliente(s,channel):
    print("Estas registrado como el cliente: "+s)
    print("Que quieres hacer: ")
    print("1: Crear Pedido")
    print("2: Ver Pedidos")
    print("3: Cancelar Pedidos")
    try:
        opcion = int(input())
        if opcion < 1 or opcion > 3:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("Opción no válida seleccione 1, 2 o 3")
            cliente(s,channel)
    except ValueError:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Opción no válida seleccione 1, 2 o 3")
        cliente(s,channel)
    except KeyboardInterrupt:
        sys.exit(0)

    
    
def registro(channel):
    os.system('cls' if os.name == 'nt' else 'clear')
    print("Introduce tu identificador de cliente: ", end ="")
    s = input()
    channel.basic_publish(exchange='', routing_key='rpc_queue',properties=pika.BasicProperties( reply_to=callback_queue, correlation_id=corr_id), body=s)

    os.system('cls' if os.name == 'nt' else 'clear')
    cliente(s,channel)

def crear_cola():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    result = channel.queue_declare(queue='login', exclusive=True, durable=False, auto_delete=True)
    callback_queue = result.method.queue

    channel.basic_consume(
        queue=callback_queue, on_message_callback=login_response_callback, auto_ack=True)

    corr_id = str(uuid.uuid4())

    return channel, connection


def login_response_callback(ch, method, props, body):
    response = body
    if(response == ERROR):
        print("Error al registrar")
    
    elif(response == OK):
        print("Cliente registrado")
    
    elif(response == REGISTERED):
        print("Cliente registrado")
    
    
def main():
    channel, connection = crear_cola()
    registro(channel)



    connection.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
