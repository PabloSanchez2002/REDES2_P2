#!/usr/bin/env python

import uuid
import pika
import psycopg2
import sys
import os

ERROR = 0
OK = 1
REGISTERED = 2

#Queues
RPC_CLIENT = "2321-02_rpc_queue_cliente"
SEND_ROBOT = "2321-02_send_to_robot"
RETURN_REBOT = "2321-02_return_from_robot"
SEND_REPARTIDOR = "2321-02_send_to_repartidor"
RETURN_REPARTIDOR = "2321-02_return_from_repartidor"

class Controlador(object):
    """Clase para el Controlador

    Args:
        object (Controlador): Se encarga de la logistica del sistema, y conectar todos los componentes entre sí mediante colas de mensajes
    """

    def __init__(self):
        """Incializador de clase
        """
        os.system('cls' if os.name == 'nt' else 'clear')                        # limpia la ventana de visualización usando cls -> windows o clear-> linux

        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))                        # Comienza una conexión bloqueante a la libreria de pika

        #Cola clientes RPC
        print("Creating queues.......")
        self.channel = self.connection.channel()                                # Comienza una conexión al canal
        self.channel.queue_declare(queue=RPC_CLIENT)                            # Declara una cola RPC entre el controlador y el cliente
        self.channel.basic_qos(prefetch_count=1)                                # Cambia el número de mensajes que trata el canal a la vez 
        self.channel.basic_consume(
            queue=RPC_CLIENT, on_message_callback=self.on_request_client)       # Indica que hará la cola en caso de recibir un mensaje
        self.channel.queue_declare(queue=SEND_ROBOT, durable=False, 
                                   auto_delete=True)
        self.channel.queue_declare(
            queue=RETURN_REBOT, durable=False, auto_delete=True)
        self.channel.basic_consume(
            queue=RETURN_REBOT,
            on_message_callback=self.on_request_robot,
            auto_ack=True)
        self.channel.queue_declare(
            queue=SEND_REPARTIDOR, durable=False, auto_delete=True)
        self.channel.queue_declare(
            queue=RETURN_REPARTIDOR, durable=False, auto_delete=True)
        self.channel.basic_consume(
            queue=RETURN_REPARTIDOR,
            on_message_callback=self.on_request_repartidor,
            auto_ack=True)
        self.corr_id = None
        if (len(sys.argv) > 1):
            if sys.argv[1] == "cleanDB":
                self.create_database()                                              # Llama a la función de limpieza de la base de datos
                self.create_tables()
        print(" [x] Esperando peticiones cliente")
        self.channel.start_consuming()
        self.connection.close()


    def create_database(self):
        """Crea la base de datos que se usará en el sistema
        """
        con = psycopg2.connect(
            database="postgres",
            user="postgres",
            password="password",
            host="localhost",
            port='5432'
        )                                                                           # Crea una conexión a la base de datos postgres
        con.autocommit = True
        cursor = con.cursor()
        cursor.execute("DROP database IF EXISTS P2Redes")                           # Borrar la base de datos
        print("Database deleted successfully........")
        cursor.execute("CREATE database P2Redes")                                   # Crear la base de datos de nuevo
        print("Database created successfully........")
        con.commit()                                                                # Hace commit a los cambios
        con.close()                                                                 # Cierra la conexión

    def create_tables(self):
        """Crea las tablas de la base de datos que será usadas en el sistema
        """
        con = psycopg2.connect(
            database="p2redes",
            user="postgres",
            password="password",
            host="localhost",
            port='5432'
        )                                                                           
        con.autocommit = True
        cursor = con.cursor()
        cursor.execute("DROP TABLE IF EXISTS CLIENTES")
        cursor.execute("""CREATE TABLE CLIENTES( 
            NOMBRE TEXT NOT NULL UNIQUE)""")
        print("Table CLIENTES created successfully........")
        cursor.execute("DROP TABLE IF EXISTS PEDIDOS")
        cursor.execute("""CREATE TABLE PEDIDOS( 
            ID SERIAL PRIMARY KEY, 
            PRODUCTO TEXT, 
            CANTIDAD INT, 
            CLIENT TEXT NOT NULL,
            STATUS TEXT NOT NULL,
            CONSTRAINT fk_cliente FOREIGN 
            KEY(CLIENT) REFERENCES CLIENTES(NOMBRE) );""")                             # La tabla de pedidos
        print("Table PEDIDOS created successfully........")
        con.commit()
        con.close()

    def on_request_client(self, ch, method, props, body):
        """Atiende una petición del cliente

        Args:
            ch (_type_): canal para el RPC
            method (_type_): metodo (no usado)
            props (_type_): info del mensaje
            body (_type_): contenido del mensaje
        """
        token = body.decode()
        print("Cli request received:" + token)
        response = ERROR
        mode = int(token[0])
        token = token[1:len(token)]
        con = psycopg2.connect(
            database="p2redes",
            user="postgres",
            password="password",
            host="localhost",
            port='5432'
        )
        cursor_obj = con.cursor()                                                   # Según el modo recibido, ejecutará una función del cliente
        if mode == 1:
            response = self.register_Client(token, con, cursor_obj)
        elif mode == 2:
            response = self.crear_Pedido(token, con, cursor_obj)
        elif mode == 3:
            response = self.listar_Pedidos(token, cursor_obj)
        elif mode == 4:
            response = self.cancelar_Pedido(token, con, cursor_obj)   
        else:
            response = ERROR                                                        # Se ha introducido un valor no válido
        con.close()
        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(
                         correlation_id=props.correlation_id),
                         body=str(response))                                        # Respuesta de la cola
        ch.basic_ack(delivery_tag=method.delivery_tag)


    def register_Client(self, token, con, cursor_obj):
        """Registra un cliente en la base de datos del dsistema

        Args:
            token (_type_): mensaje a procesar
            con (_type_): interfaz postres
            cursor_obj (_type_): cursor postgres

        Returns:
            int: OK/ERROR
        """
        cursor_obj.execute(
                "SELECT COUNT(*) as count FROM CLIENTES WHERE NOMBRE = \'" + 
                token + "\'")
        result = cursor_obj.fetchall()
        if (len(result) > 1):                                                   # Este caso nunca debería aparecer a no ser que se modifique la bd de alguna forma exterior a el programa 
            return ERROR
        elif (result[0][0] == 0):
            cursor_obj.execute(
                "INSERT INTO CLIENTES VALUES (\'" + token + "\')")
            con.commit()
            return REGISTERED                                                   # Estado de registrado
        elif (result[0][0] == 1):
            return OK                                                           # Estado de usuario ya creado, (login)
        else:
            return ERROR                                                        # Estado de ERROR, no debería de suceder


    def crear_Pedido(self, token, con, cursor_obj):
        """Crea un pedido para un cliente

        Args:
            token (_type_): mensaje a procesar
            con (_type_): interfaz postres
            cursor_obj (_type_): cursor postgres

        Returns:
            int: respuesta del envío del robot
        """
        list_tokens = token.split("|")
        print("Pedido recibido: "+str(list_tokens))
        cursor_obj.execute(
                "INSERT INTO PEDIDOS VALUES (DEFAULT ,\'" + 
                list_tokens[0] + "\', \'" + list_tokens[1] + "\', \'" + 
                list_tokens[2] + "\', 'PROCESSING') RETURNING ID")            # Se crea el pedido a añadir
        result = cursor_obj.fetchall()
        con.commit()
        return self.send_Robot(result[0][0])                                  # Se envia la información al robot (pedido registrado, se pone en funcionamiento)
         
    def listar_Pedidos(self, token, cursor_obj):
        """Retorna la lista de pedidos asociados a este cliente

        Args:
            token (_type_): mensaje a procesar
            cursor_obj (_type_): cursor postgres

        Returns:
            str: lista de pedidos asociados a este cliente
        """
        cursor_obj.execute(
            "SELECT * FROM PEDIDOS WHERE CLIENT = \'" + token + "\'")
        return cursor_obj.fetchall()                                         # Se devuelven los pedidos del cliente

    def cancelar_Pedido(self, token, con, cursor_obj):
        """Cancela un pedido si todavía es posible

        Args:
            token (_type_): mensaje a procesar
            con (_type_): interfaz postres
            cursor_obj (_type_): cursor postgres

        Returns:
            int: OK/ERROR
        """
        list_tokens = token.split("|")
        cursor_obj.execute(
                "SELECT COUNT(*) as count FROM PEDIDOS WHERE CLIENT = \'" + 
                list_tokens[0] + "\' AND ID = \'" + 
                list_tokens[1] + "\' AND STATUS <> 'PROCESSING'")
        result = cursor_obj.fetchall()
        if (result[0][0] >= 1):
            return ERROR
        else:
            cursor_obj.execute(
                "UPDATE PEDIDOS SET STATUS = 'CANCELLED' WHERE CLIENT = \'" + 
                list_tokens[0] + "\' AND ID = \'" + 
                list_tokens[1] + "\' AND STATUS = 'PROCESSING'")
            con.commit()
            return OK
        
    def send_Robot(self, id):
        """Sends message to robot

        Args:
            id (int): ID del pedido

        Returns:
            int: OK
        """
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='', routing_key=SEND_ROBOT, body=str(id))              # Se envía la información a la cola del Robot
        return OK

    def on_request_robot(self, ch, method, props, body):
        """Callback de respuesta del robot

        Args:
            ch (_type_): canal de referencia
            method (_type_): metodo (no usado)
            props (_type_): info del mensaje
            body (_type_): contenido del mensaje
        """
        print("Respuesta del robot: %r" % body.decode())
        list_tokens = body.decode().split("|")
        mode = int(list_tokens[0])
        token = list_tokens[1]
        con = psycopg2.connect(
            database="p2redes",
            user="postgres",
            password="password",
            host="localhost",
            port='5432'
        )
        cursor_obj = con.cursor()

        cursor_obj.execute(
                "SELECT COUNT(*) as count FROM PEDIDOS WHERE ID = \'" + 
                token + "\' AND STATUS = 'CANCELLED'")
        result = cursor_obj.fetchall()
        if (result[0][0] == 1):
            print("El pedido fue cancelado antes de empaquetarse")          # Caso de que el pedido se halla cancelado mientras que el repartidor buscaba
        else:
            if mode == 1:
                print("El robot encontró el pedido ")                       # Se encontro el pedido
                cursor_obj.execute(
                        "UPDATE PEDIDOS SET STATUS = 'PACKED' WHERE ID = \'" + 
                        token + "\' AND STATUS = 'PROCESSING'")
                self.send_Repartidor(token, 0)

            elif mode == 0:
                print("El robot NO encontró el pedido ")                    # No se ha encontrado el pedido
                cursor_obj.execute(
                        "UPDATE PEDIDOS SET STATUS = 'NOTFOUND' WHERE ID = \'" + 
                        token + "\' AND STATUS = 'PROCESSING'")
        con.commit()
        con.close()
        return

    def send_Repartidor(self, id, tries):
        """Envio de mensaje al repartidor

        Args:
            id (int): ID del pedido
            tries (int): número de intentos de entrega (de 0 hasta 2)

        Returns:
            int: OK
        """
        send = id + "|" + str(tries)
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='', routing_key=SEND_REPARTIDOR, body=send)            # Enviar mensaje a el repartidor
        return OK

    def on_request_repartidor(self, ch, method, props, body):
        """Callback de respuesta a mensaje del repartidor

        Args:
            ch (_type_): canal de referencia
            method (_type_): metodo (no usado)
            props (_type_): info del mensaje
            body (_type_): contenido del mensaje
        """
        print("Respuesta del repartidor: %r" % body.decode())
        list_tokens = body.decode().split("|") 
        mode = int(list_tokens[0])
        con = psycopg2.connect(
            database="p2redes",
            user="postgres",
            password="password",
            host="localhost",
            port='5432'
        )
        cursor_obj = con.cursor()
        if mode == 1:
            print("Se entregó el paquete ID = " + list_tokens[1])
            cursor_obj.execute(
                    "UPDATE PEDIDOS SET STATUS = 'DELIVERED' WHERE ID = \'" + 
                    list_tokens[1] + "\' AND STATUS = 'PACKED'")
        elif mode == 0:
            print("Fallo de entrega del paquete ID = " + list_tokens[1])
            if int(list_tokens[2]) >= 2:
                print("Se gotaron todos los intentos")
                cursor_obj.execute(
                        "UPDATE PEDIDOS SET STATUS = 'NOTDELIVERED' WHERE ID = \'" + 
                        list_tokens[1] + "\' AND STATUS = 'PACKED'")
            else:
                print("Se procede a reintentar entrega")
                list_tokens[2] = int(list_tokens[2]) +1
                self.send_Repartidor(list_tokens[1], list_tokens[2])
        
        con.commit()
        con.close()
        return


def main():
    """Punto de entrada del programa
    """
    controlador = Controlador()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
