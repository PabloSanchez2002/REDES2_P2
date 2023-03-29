#!/usr/bin/env python
import os
import sys
import uuid
import pika
import time

ERROR = 0
OK = 1
REGISTERED = 2


class Client(object):

    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))

        self.channel = self.connection.channel()
        self.nombre = None

        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)

        self.response = None
        self.corr_id = None

    def menu(self):
        print("Estas registrado como el cliente: "+ self.nombre)
        print("Que quieres hacer: ")
        print("1: Crear Pedido")
        print("2: Ver Pedidos")
        print("3: Cancelar Pedidos")
        try:
            opcion = int(input())
            if opcion < 1 or opcion > 3:
                os.system('cls' if os.name == 'nt' else 'clear')
                print("Opción no válida seleccione 1, 2 o 3")
                self.menu()
            elif opcion == 1:
                self.new_pedido()
            elif opcion == 2:
                self.ver_pedidos()
            elif opcion == 3:
                self.cancelar_pedido()

        except ValueError:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("Opción no válida seleccione 1, 2 o 3")
            self.menu()
        except KeyboardInterrupt:
            sys.exit(0)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def login(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        self.response = None
        self.corr_id = str(uuid.uuid4())
        print("Introduce tu identificador de cliente: ", end="")
        s = input()
        self.nombre = s
        s = ("1"+s)
        self.channel.basic_publish(
            exchange='',
            routing_key='rpc_queue',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=s)
        self.connection.process_data_events(time_limit=None)
        return self.response

        

    def login_response(self, response):
        response = int(response)
        if (response == ERROR):
            print("Error al registrar")

        elif (response == OK):
            print("Log in completo")
            self.menu()

        elif (response == REGISTERED):
            print("Cliente registrado")
            self.menu()
        else:
            print("Error en respuesta, se recibio:" + response)

    def new_pedido(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Introduce el nombre del producto: ", end="")
        product = input()
        print("Introduce la cantidad del producto: ", end="")
        cantidad = input()
        pedido = ("2" + product + "|" + cantidad + "|" + self.nombre)

        self.channel.basic_publish(
            exchange='',
            routing_key='rpc_queue',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=pedido)
        self.connection.process_data_events(time_limit=None)

        print("Pedido enviado!!")
        self.connection.process_data_events(time_limit=None)
        return self.response




def main():
    cliente = Client()
    response = cliente.login()
    cliente.login_response(str(response.decode()))
    cliente.connection.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
