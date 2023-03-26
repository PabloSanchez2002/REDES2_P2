import pika
import psycopg2
import sys
import os

ERROR = 0
OK = 1
REGISTERED = 2

def create_database():
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
    sql = '''DROP database P2Redes'''
    # Drop database
    cursor.execute(sql)
    # Preparing query to create a database
    sql = '''CREATE database P2Redes'''
    # Creating a database
    cursor.execute(sql)
    print("Database created successfully........")

    cursor.execute("DROP TABLE IF EXISTS PEDIDOS")
    # Creating table as per requirement
    sql = '''CREATE TABLE PEDIDOS(
    ID CHAR(20) NOT NULL,
    PRODUCTO CHAR(20),
    CANTIDAD INT
    )'''
    
    cursor.execute(sql)
    print("Table PEDIDOS created successfully........")

    # Creating table as per requirement
    sql = '''CREATE TABLE CLIENTES(
    NOMBRE CHAR(30) NOT NULL
    )'''

    cursor.execute(sql)
    print("Table CLIENTES created successfully........")

    con.commit()
    # Closing the connection
    con.close()

def login_client(nombre):
    con = psycopg2.connect(
        database="P2Redes",
        user="",
        password="",
        host="localhost",
        port='5432'
    )
    cursor_obj = con.cursor()
    cursor_obj.execute(
        "SELECT COUNT(*) as count FROM CLIENTES WHERE NOMBRE = \"" + nombre + "\"")
    con.commit()
    result = cursor_obj.fetchall()

    if (len(result) > 1):

        # Closing the connection
        con.close()
        return ERROR
        #Mandamos mensaje de error
    
    elif(len(result) == 0):
        cursor_obj.execute("INSERT INTO CLIENTES VALUES (\"" + nombre + "\")")
        con.commit()
        # Closing the connection
        con.close()
        return REGISTERED

    elif (result[0][0] == 1):

        # Closing the connection
        con.close()
        return OK
    else:
        return ERROR
    
    

def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='login', exclusive=True,
                          durable=False, auto_delete=True)

    def rpc_login_client(ch, method, props, body):
        response = login_client(body)  # Perform the desired operation
        ch.basic_publish(exchange='',
                        routing_key=props.reply_to,
                        properties=pika.BasicProperties(
                            correlation_id=props.correlation_id),
                        body=str(response))
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue='login', on_message_callback=rpc_login_client)

    create_database()

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
