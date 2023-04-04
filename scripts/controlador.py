#!/usr/bin/env python
import time
import uuid
import pika
import psycopg2
import sys
import os
import _thread


ERROR = 0
OK = 1
REGISTERED = 2

class Controlador(object):
    def __init__(self):
        os.system('cls' if os.name == 'nt' else 'clear')

        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))

        #Cola clientes RPC
        print("Creating queues.......")
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='rpc_queue_cliente')
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue='rpc_queue_cliente', on_message_callback=self.on_request_client)
        
        # Cola envío robots
        self.channel.queue_declare(queue='send_to_robot', durable=False, auto_delete=True)
        
        # Cola respuesta robots
        self.channel.queue_declare(
            queue='return_from_robot', durable=False, auto_delete=True)
        self.channel.basic_consume(
            queue='return_from_robot',
            on_message_callback=self.on_request_robot,
            auto_ack=True)

        # Cola envío repartidor
        self.channel.queue_declare(
            queue='send_to_repartidor', durable=False, auto_delete=True)

        # Cola respuesta repartidor
        self.channel.queue_declare(
            queue='return_from_repartidor', durable=False, auto_delete=True)
        self.channel.basic_consume(
            queue='return_from_repartidor',
            on_message_callback=self.on_request_repartidor,
            auto_ack=True)


        self.corr_id = None

        #try:
        #    _thread.start_new_thread(self.gestionar_Queues, (0,))
        #except Exception as e:
        #    print("Error: unable to start thread")
        #    print(e)

        self.create_database()
        self.create_tables()
        print(" [x] Esperando peticiones cliente")
        self.channel.start_consuming()

    def gestionar_Queues(self, useless):
        while True:
            self.channel.connection.process_data_events(time_limit=1)
            self.channel.connection.process_data_events(time_limit=1)

    def create_database(self):
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

        cursor.execute("CREATE TABLE CLIENTES( \
            NOMBRE TEXT NOT NULL UNIQUE)")
        print("Table CLIENTES created successfully........")

        cursor.execute("DROP TABLE IF EXISTS PEDIDOS")
        # Creating table as per requirement

        cursor.execute("CREATE TABLE PEDIDOS( \
            ID SERIAL PRIMARY KEY, \
            PRODUCTO TEXT, \
            CANTIDAD INT, \
            CLIENT TEXT NOT NULL,\
            STATUS TEXT NOT NULL,\
            CONSTRAINT fk_cliente FOREIGN KEY(CLIENT) REFERENCES CLIENTES(NOMBRE) );")
        print("Table PEDIDOS created successfully........")



        con.commit()
        # Closing the connection
        con.close()

    def on_request_client(self, ch, method, props, body):
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
        cursor_obj.execute(
            "SELECT COUNT(*) as count FROM CLIENTES WHERE NOMBRE = \'" + token + "\'")
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

        list_tokens = token.split("|")
        print("Pedido recibido: "+str(list_tokens))
        cursor_obj.execute(
            "INSERT INTO PEDIDOS VALUES (DEFAULT ,\'" + list_tokens[0] + "\', \'" + list_tokens[1] + "\', \'" + list_tokens[2] + "\', 'PROCESSING') RETURNING ID")
        result = cursor_obj.fetchall()
        con.commit()
        # We send a mesasge to the rebot
        return self.send_Robot(result[0][0])
         
        
    
    def listar_Pedidos(self, token, cursor_obj):
        cursor_obj.execute(
            "SELECT * FROM PEDIDOS WHERE CLIENT = \'" + token + "\'")
        return cursor_obj.fetchall()

    def cancelar_Pedido(self, token, con, cursor_obj):
        list_tokens = token.split("|")
        cursor_obj.execute(
              "SELECT COUNT(*) as count FROM PEDIDOS WHERE CLIENT = \'" + list_tokens[0] + "\' AND ID = \'" + list_tokens[1] + "\' AND STATUS <> 'PROCESSING'")
        result = cursor_obj.fetchall()
        if (result[0][0] >= 1):
            return ERROR
        else:
            cursor_obj.execute(
                "UPDATE PEDIDOS SET STATUS = 'CANCELLED' WHERE CLIENT = \'" + list_tokens[0] + "\' AND ID = \'" + list_tokens[1] + "\' AND STATUS = 'PROCESSING'")
            con.commit()
            return OK
        

    def send_Robot(self, id):
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='', routing_key='send_to_robot', body=str(id))
        return OK


    def on_request_robot(self, ch, method, props, body):
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
            "SELECT COUNT(*) as count FROM PEDIDOS WHERE ID = \'" + token + "\' AND STATUS = 'CANCELLED'")
        result = cursor_obj.fetchall()
        if (result[0][0] == 1):
            print("El pedido fue cancelado antes de empaquetarse")
            
        else:
            if mode == 1:
                print("El robot encontró el pedido ")
                cursor_obj.execute(
                    "UPDATE PEDIDOS SET STATUS = 'PACKED' WHERE ID = \'" + token + "\' AND STATUS = 'PROCESSING'")
                self.send_Repartidor(token, 0)

            elif mode == 0:
                print("El robot NO encontró el pedido ")
                cursor_obj.execute(
                    "UPDATE PEDIDOS SET STATUS = 'NOTFOUND' WHERE ID = \'" + token + "\' AND STATUS = 'PROCESSING'")
        con.commit()
        con.close()
        return

    def send_Repartidor(self, id, tries):
        send = id + "|" + str(tries)
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='', routing_key='send_to_repartidor', body=send)
        return OK

    def on_request_repartidor(self, ch, method, props, body):
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
                "UPDATE PEDIDOS SET STATUS = 'DELIVERED' WHERE ID = \'" + list_tokens[1] + "\' AND STATUS = 'PACKED'")
        
        elif mode == 0:
            print("Fallo de entrega del paquete ID = " + list_tokens[1])
            if int(list_tokens[2]) >= 2:
                print("Se gotaron todos los intentos")
                cursor_obj.execute(
                    "UPDATE PEDIDOS SET STATUS = 'NOTDELIVERED' WHERE ID = \'" + list_tokens[1] + "\' AND STATUS = 'PACKED'")
            else:
                print("Se procede a reintentar entrega")
                list_tokens[2] = int(list_tokens[2]) +1
                self.send_Repartidor(list_tokens[1], list_tokens[2])
        
        con.commit()
        con.close()
        return


def main():
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
