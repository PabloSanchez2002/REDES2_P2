#!/usr/bin/env python
import pika
import sys
import os
import time
import random


ERROR = 0
OK = 1
REGISTERED = 2
MAX_T = 20
MIN_T = 10
p_entrega = 0.3

SEND_REPARTIDOR = "2321-02_send_to_repartidor"
RETURN_REPARTIDOR = "2321-02_return_from_repartidor"


class Delivery(object):
    """Clase Repartidor, se encarga derepartir un pedido

    Args:
        object (_type_): reparte un pedido
    """
    def __init__(self) -> None:
        """Inicializador de clase
        """
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='redes2.ii.uam.es'))
        self.channel = self.connection.channel()
        self.channel.queue_declare(
            queue=SEND_REPARTIDOR, durable=False, auto_delete=True)
        self.channel.basic_consume(
            queue=SEND_REPARTIDOR, on_message_callback=self.on_response, auto_ack=True)
        self.channel.queue_declare(
            queue=RETURN_REPARTIDOR, durable=False, auto_delete=True)
        print("Repartidor operativo....")
        self.channel.start_consuming()
        self.connection.close()

    def on_response(self, ch, method, props, body):
        """Callback de peticion del controlador

        Args:
            ch (_type_): canal de referencia
            method (_type_): metodo (no usado)
            props (_type_): info del mensaje
            body (_type_): contenido del mensaje
        """
        list_tokens = body.decode().split("|")
        tiempo_espera = random.uniform(MAX_T, MIN_T)
        intento = str(int(list_tokens[1]) + 1)                                          # Numero de intentos realizados
        print(intento + "º intento de entrega del pedido Nº" +
              list_tokens[0] + " durante" + f"{tiempo_espera: .2f} segundos... ")        
        time.sleep(tiempo_espera)
        if random.random() < p_entrega:                                                 # Calculo de tiempo de entrega
            print("Pedido entregado")
            response = "1|" + body.decode()
        else:
            print("Pedido no entregado")
            response = "0|" + body.decode()
        self.channel.basic_publish(
            exchange='', routing_key=RETURN_REPARTIDOR, body=str(response))             # Envio de mensaje a controlador
        print(" [x] Enviado %r" % response)

def main():
    """Punto de entrada de ejecución
    """
    repart = Delivery()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
