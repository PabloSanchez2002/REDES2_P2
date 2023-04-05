#!/usr/bin/env python
import os
import sys
import uuid
import pika

ERROR = 0
OK = 1
REGISTERED = 2

RPC_CLIENT = "2321-02_rpc_queue_cliente"

class Client(object):
    """Clase cliente del sistema

    Args:
        object (_type_): se loggea, realiza, consulta y cancela pedidos.
    """

    def __init__(self):
        """Inicializador de clase
        """
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))

        self.channel = self.connection.channel()
        result = self.channel.queue_declare(
            queue='', exclusive=True, durable=False, auto_delete=True)
        self.callback_queue = result.method.queue
        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)
        

        self.nombre = None
        self.corr_id = None
        self.response = None
        
        self.login_response(str(self.login().decode()))
        self.connection.close()

    def on_response(self, ch, method, props, body):
        """Callback de la cola RPC

        Args:
            ch (_type_): canal de referencia
            method (_type_): metodo (no usado)
            props (_type_): info del mensaje
            body (_type_): contenido del mensaje
        """
        if self.corr_id == props.correlation_id:
            self.response = body

    def menu(self):
        """Función de menu por consola para el cliente
        """
        print("//--------------------------------------//")
        print("Estas registrado como el cliente: "+ self.nombre + "\n")
        print("Que quieres hacer: ")
        print("1: Crear Pedido")
        print("2: Ver Pedidos")
        print("3: Cancelar Pedidos")
        print("Introduce numero: ", end="")
        try:
            opcion = int(input())

            if opcion < 1 or opcion > 3:
                os.system('cls' if os.name == 'nt' else 'clear')
                print("Opción no válida seleccione 1, 2 o 3")
                self.menu()

            elif opcion == 1:
                response = int(self.new_pedido())
                if(response == OK):
                    print("Pedido recibido por el controlador\n")
                else:
                    print("Error al recibir pedido\n")
                self.menu()

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

    

    def login(self):
        """Funcion de login/signup

        Returns:
            _type_: respuesta del controlador
        """
        os.system('cls' if os.name == 'nt' else 'clear')
        self.response = None
        self.corr_id = str(uuid.uuid4())
        print("Introduce tu identificador de cliente: ", end="")
        s = input()
        self.nombre = s
        s = ("1"+s)
        self.channel.basic_publish(
            exchange='',
            routing_key=RPC_CLIENT,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=s)
        self.connection.process_data_events(time_limit=None)
        return self.response

        
    def login_response(self, response):
        """Función que valida la respuesta del controlador

        Args:
            response (int): codigo de respuesta del controlador
        """
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
        """Crea un nuevo pedido para el cliente

        Returns:
            _type_: respuesta del controlador
        """
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Introduce el nombre del producto: ", end="")
        product = input()
        print("Introduce la cantidad del producto: ", end="")
        cantidad = input()
        pedido = ("2" + product + "|" + cantidad + "|" + self.nombre)

        self.channel.basic_publish(
            exchange='',
            routing_key=RPC_CLIENT,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=pedido)
        self.connection.process_data_events(time_limit=None)

        print("Pedido enviado!!")
        print("Mira tus pedidos con '2' para obtener información del estado de estos")
        return self.response

    def ver_pedidos(self):
        """Pregunta al servidor por los pedidos que tiene a su nombre, y los muestra por terminal 
        """
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Ver pedidos")
        pedido = ("3" + self.nombre)

        self.channel.basic_publish(
            exchange='',
            routing_key=RPC_CLIENT,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=pedido)
        self.connection.process_data_events(time_limit=None)

        pedidos = self.response.decode()
        print("ID  | Producto | Cantidad | Cliente | Estado ")
        pedidos = eval(pedidos)
        for pedido in pedidos:
            print("{:<4}".format(str(pedido[0])) + "| " + "{:<9}".format(str(pedido[1])) + "| " + "{:<9}".format(
                str(pedido[2])) + "| " + "{:<8}".format(str(pedido[3])) + "| " + str(pedido[4]))

        self.menu()

    def cancelar_pedido(self):
        """Cancela un pedido del cliente
        """
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Cancelar pedido")
        print("Introduce indice de pedido que quieras cancelar: ", end = "")
        id = input()
        pedido = ("4" + self.nombre + "|" + id)

        self.channel.basic_publish(
            exchange='',
            routing_key=RPC_CLIENT,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=pedido)
        self.connection.process_data_events(time_limit=None)
        if (int(self.response.decode()) == OK):
            print("Pedido cancelado correctamente")
        else:
            print("Error al cancelar pedido")
        self.menu()


def main():
    """Punto de entrada de ejecución
    """
    cliente = Client()
    
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
