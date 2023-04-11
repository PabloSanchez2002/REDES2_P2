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
p_almacen = 0.5

SEND_ROBOT = "2321-02_send_to_robot"
RETURN_REBOT = "2321-02_return_from_robot"


class Robot(object):
    """Clase Robot encargado de empaquetar un pedido

    Args:
        object (_type_): empaqueta pedido
    """
    def __init__(self) -> None:
        """Inicia.izador de clase
        """
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='redes2.ii.uam.es'))
        self.channel = self.connection.channel()
        self.channel.queue_declare(
            queue=SEND_ROBOT, durable=False, auto_delete=True)
        self.channel.basic_consume(
            queue=SEND_ROBOT, on_message_callback=self.on_response, \
            auto_ack=True)
        self.channel.queue_declare(
            queue=RETURN_REBOT, durable=False, auto_delete=True)
        print("Robot operativo....")
        self.channel.start_consuming()
        self.connection.close()

    def on_response(self, ch, method, props, body):
        """Callback de la peticion del controlador
        Args:
            ch (_type_): canal de referencia
            method (_type_): metodo (no usado)
            props (_type_): info del mensaje
            body (_type_): contenido del mensaje
        """
        tiempo_espera = random.uniform(MAX_T, MIN_T)                                # Tiempo por que tardará en buscar el pedido
        print("Buscando el pedido Nº" + body.decode() +
              " durante" + f"{tiempo_espera: .2f} segundos...")
        time.sleep(tiempo_espera)
        if random.random() < p_almacen:                                             # Calculo de encontrado o no
            print("Pedido encontrado")
            response = "1|" + body.decode()
        else:
            print("Pedido no encontrado")
            response = "0|" + body.decode()

        self.channel.basic_publish(
            exchange='', routing_key=RETURN_REBOT, body=str(response))              # Envio mensaje a controlador
        print(" [x] Enviado %r" % response)
              

def main():
    """Punto de entrada de ejecución
    """
    rob = Robot()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
