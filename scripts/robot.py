#!/usr/bin/env python
import pika
import sys
import os
import time
import random


ERROR = 0
OK = 1
REGISTERED = 2

MAX_T = 5
MIN_T = 1
p_almacen = 0.1


class robot(object):
    def __init__(self) -> None:
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))

        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='rpc_queue_robot')
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue='rpc_queue_robot', on_message_callback=self.on_response)
        
        
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Robot operativo....")

        self.channel.start_consuming()
        #self.connection.close()

    def on_response(self, ch, method, props, body):
        tiempo_espera = random.uniform(MAX_T, MIN_T)
        print(f"Buscando el pedido durante {tiempo_espera:.2f} segundos...")
        time.sleep(tiempo_espera)
        if random.random() < p_almacen:
            print("Pedido encontrado")
            return OK
        else:
            print("Pedido no encontrado")
            return ERROR
        
              

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
