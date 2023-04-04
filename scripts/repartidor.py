#!/usr/bin/env python
import pika
import sys
import os
import time
import random


ERROR = 0
OK = 1
REGISTERED = 2
#espera de 10-20s
MAX_T = 5
MIN_T = 1
p_entrega = 0.1


class repartidor(object):
    def __init__(self) -> None:
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))

        # Peticion
        self.channel1 = self.connection.channel()
        self.channel1.queue_declare(queue='send_to_repartidor')
        self.channel1.basic_consume(
            queue='send_to_repartidor', on_message_callback=self.on_response, auto_ack=True)

        # Respuesta
        self.channel2 = self.connection.channel()
        self.channel2.queue_declare(queue='return_from_repartidor')

        os.system('cls' if os.name == 'nt' else 'clear')
        print("Repartidor operativo....")

        self.channel1.start_consuming()
        # self.connection.close()

    def on_response(self, ch, method, props, body):
        list_tokens = body.decode().split("|")
        tiempo_espera = random.uniform(MAX_T, MIN_T)
        intento = str(int(list_tokens[1]) + 1)
        print(intento + "º intento de entrega del pedido Nº" +
              list_tokens[0] + " durante" + f"{tiempo_espera: .2f} segundos... ")
        time.sleep(tiempo_espera)
        if random.random() < p_entrega:
            print("Pedido entrgado")
            response = "1|" + body.decode()
        else:
            print("Pedido no entregado")
            response = "0|" + body.decode()

        self.channel2.basic_publish(
            exchange='', routing_key='return_from_repartidor', body=str(response))
        print(" [x] Enviado %r" % response)

def main():
    repart = repartidor()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
