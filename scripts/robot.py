#!/usr/bin/env python
import pika
import sys
import os
import time
import random


ERROR = 0
OK = 1
REGISTERED = 2
#espera 5-10s
MAX_T = 5
MIN_T = 1
p_almacen = 0.5


class robot(object):
    def __init__(self) -> None:
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))
        
        # Peticion
        self.channel = self.connection.channel()
        self.channel.queue_declare(
            queue='send_to_robot', durable=False, auto_delete=True)
        self.channel.basic_consume(
            queue='send_to_robot', on_message_callback=self.on_response, auto_ack=True)
        
        # Respuesta
        self.channel.queue_declare(
            queue='return_from_robot', durable=False, auto_delete=True)
       

        os.system('cls' if os.name == 'nt' else 'clear')
        print("Robot operativo....")

        self.channel.start_consuming()
        #self.connection.close()

    def on_response(self, ch, method, props, body):

        tiempo_espera = random.uniform(MAX_T, MIN_T)
        print("Buscando el pedido Nº" + body.decode() +
              " durante" + f"{tiempo_espera: .2f} segundos...")
        time.sleep(tiempo_espera)
        if random.random() < p_almacen:
            print("Pedido encontrado")
            response = "1|" + body.decode()
        else:
            print("Pedido no encontrado")
            response = "0|" + body.decode()

        self.channel.basic_publish(
            exchange='', routing_key='return_from_robot', body=str(response))
        print(" [x] Enviado %r" % response)
              

def main():
    rob = robot()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
