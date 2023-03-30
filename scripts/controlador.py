#!/usr/bin/env python
import pika
import psycopg2
import sys
import os

ERROR = 0
OK = 1
REGISTERED = 2

class Controlador(object):
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))

        self.channel1 = self.connection.channel()

        self.channel1.queue_declare(queue='rpc_queue_cliente')
        self.channel1.basic_qos(prefetch_count=1)
        self.channel1.basic_consume(
            queue='rpc_queue_cliente', on_message_callback=on_request)
        create_database()
        create_tables()
        print(" [x] Awaiting RPC requests")
        self.channel1.start_consuming()


def create_database():
    os.system('cls' if os.name == 'nt' else 'clear')
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

def create_tables():
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

def on_request(ch, method, props, body):
    token = body.decode()
    print("Request received:" + token)
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
        cursor_obj.execute(
            "SELECT COUNT(*) as count FROM CLIENTES WHERE NOMBRE = \'" + token + "\'")
        result = cursor_obj.fetchall()
        if (len(result) > 1):
           # Closing the connection
           con.close()
           # Mandamos mensaje de error
        elif (result[0][0] == 0):
           cursor_obj.execute("INSERT INTO CLIENTES VALUES (\'" + token + "\')")
           con.commit()
           # Closing the connection
           con.close()
           response = REGISTERED
        elif (result[0][0] == 1):
           # Closing the connection
           con.close()
           response = OK
        else:
           response = ERROR
    elif mode == 2:
        list_tokens = token.split("|")
        print("Pedido recibido: "+str(list_tokens))
        cursor_obj.execute(
            "INSERT INTO PEDIDOS VALUES (DEFAULT ,\'" + list_tokens[0] + "\', \'" + list_tokens[1] + "\', \'" + list_tokens[2] + "\', 'PROCESSING')")
        con.commit()
        response = OK

    elif mode == 3:
        cursor_obj.execute(
            "SELECT * FROM PEDIDOS WHERE CLIENT = \'" + token + "\'")
        response = cursor_obj.fetchall()
        
    elif mode == 4:
        list_tokens = token.split("|")
        # count entryes in table pedidos where where client = list_tokens[0] and ID = list_tokens[1] and status is PROCESSING
        cursor_obj.execute(
            "SELECT COUNT(*) as count FROM PEDIDOS WHERE CLIENT = \'" + list_tokens[0] + "\' AND ID = \'" + list_tokens[1] + "\' AND STATUS <> 'PROCESSING'")
        result = cursor_obj.fetchall()
        if (result[0][0] >=1):
            response = ERROR
        else:
            cursor_obj.execute(
                "UPDATE PEDIDOS SET STATUS = 'CANCELLED' WHERE CLIENT = \'" + list_tokens[0] + "\' AND ID = \'" + list_tokens[1] + "\' AND STATUS = 'PROCESSING'")
            response = OK
        con.commit()    
        
        

        

    else:
        response = ERROR
    
    con.close()

    ch.basic_publish(exchange='',
                        routing_key=props.reply_to,
                        properties=pika.BasicProperties(
                            correlation_id=props.correlation_id),
                        body=str(response))
    ch.basic_ack(delivery_tag=method.delivery_tag)


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
