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
        os.system('cls' if os.name == 'nt' else 'clear')

        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))

        #Cola clientes RPC
        print("Creating queues.......")
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=RPC_CLIENT)
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=RPC_CLIENT, on_message_callback=self.on_request_client)
        
        # Cola envío robots
        self.channel.queue_declare(queue=SEND_ROBOT, durable=False, 
                                   auto_delete=True)
        
        # Cola respuesta robots
        self.channel.queue_declare(
            queue=RETURN_REBOT, durable=False, auto_delete=True)
        self.channel.basic_consume(
            queue=RETURN_REBOT,
            on_message_callback=self.on_request_robot,
            auto_ack=True)

        # Cola envío repartidor
        self.channel.queue_declare(
            queue=SEND_REPARTIDOR, durable=False, auto_delete=True)

        # Cola respuesta repartidor
        self.channel.queue_declare(
            queue=RETURN_REPARTIDOR, durable=False, auto_delete=True)
        self.channel.basic_consume(
            queue=RETURN_REPARTIDOR,
            on_message_callback=self.on_request_repartidor,
            auto_ack=True)


        self.corr_id = None

        if (len(sys.argv) > 1):
            if sys.argv[1] == "cleanDB":
                self.create_database()
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
        )

        con.autocommit = True

        # Creating a cursor object using the cursor() method
        cursor = con.cursor()
        # Drop database
        cursor.execute("DROP database IF EXISTS P2Redes")
        print("Database deleted successfully........")

        # Preparing query to create a database
        
        # Creating a database
        cursor.execute("CREATE database P2Redes")
        print("Database created successfully........")

        con.commit()
        # Closing the connection
        con.close()

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

        # Creating a cursor object using the cursor() method
        cursor = con.cursor()

        cursor.execute("DROP TABLE IF EXISTS CLIENTES")

        # Creating table as per requirement

        cursor.execute("""CREATE TABLE CLIENTES( 
            NOMBRE TEXT NOT NULL UNIQUE)""")
        print("Table CLIENTES created successfully........")

        cursor.execute("DROP TABLE IF EXISTS PEDIDOS")
        # Creating table as per requirement

        cursor.execute("""CREATE TABLE PEDIDOS( 
            ID SERIAL PRIMARY KEY, 
            PRODUCTO TEXT, 
            CANTIDAD INT, 
            CLIENT TEXT NOT NULL,
            STATUS TEXT NOT NULL,
            CONSTRAINT fk_cliente FOREIGN 
            KEY(CLIENT) REFERENCES CLIENTES(NOMBRE) );""")
        print("Table PEDIDOS created successfully........")



        con.commit()
        # Closing the connection
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
        cursor_obj = con.cursor()

        if mode == 1:
            response = self.register_Client(token, con, cursor_obj)

        elif mode == 2:
            response = self.crear_Pedido(token, con, cursor_obj)

        elif mode == 3:
            response = self.listar_Pedidos(token, cursor_obj)
        
        elif mode == 4:
            response = self.cancelar_Pedido(token, con, cursor_obj)   
            
        else:
            response = ERROR
        
        con.close()

        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(
                             correlation_id=props.correlation_id),
                         body=str(response))
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
        if (len(result) > 1):
            return ERROR
        elif (result[0][0] == 0):
            cursor_obj.execute(
                "INSERT INTO CLIENTES VALUES (\'" + token + "\')")
            con.commit()
            return REGISTERED
        elif (result[0][0] == 1):
            return OK
        else:
            return ERROR


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
                list_tokens[2] + "\', 'PROCESSING') RETURNING ID")
        result = cursor_obj.fetchall()
        con.commit()
        # We send a mesasge to the rebot
        return self.send_Robot(result[0][0])
         
        
    
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
        return cursor_obj.fetchall()

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
            exchange='', routing_key=SEND_ROBOT, body=str(id))
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

        # Comporbamos que el pedido no ha sido cancelado previamente
        cursor_obj.execute(
                "SELECT COUNT(*) as count FROM PEDIDOS WHERE ID = \'" + 
                token + "\' AND STATUS = 'CANCELLED'")
        result = cursor_obj.fetchall()
        if (result[0][0] == 1):
            print("El pedido fue cancelado antes de empaquetarse")
            
        else:
            if mode == 1:
                print("El robot encontró el pedido ")
                cursor_obj.execute(
                        "UPDATE PEDIDOS SET STATUS = 'PACKED' WHERE ID = \'" + 
                        token + "\' AND STATUS = 'PROCESSING'")
                self.send_Repartidor(token, 0)

            elif mode == 0:
                print("El robot NO encontró el pedido ")
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
            exchange='', routing_key=SEND_REPARTIDOR, body=send)
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
        list_tokens = body.decode().split("|") #[0] = error/OK [1] = ID [2] = intento
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
