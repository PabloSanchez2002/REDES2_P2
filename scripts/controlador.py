import pika
import psycopg2
import sys
import os

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
    print("Table created successfully........")
    con.commit()
    # Closing the connection
    con.close()

    # Closing the connection
    con.close()

def new_client():
    con = psycopg2.connect(
        database="P2Redes",
        user="",
        password="",
        host="localhost",
        port='5432'
    )
    cursor_obj = con.cursor()
    cursor_obj.execute("SELECT * FROM bike_details")
    result = cursor_obj.fetchall()
    

def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='hello')

    def callback(ch, method, properties, body):
        print(" [x] Received %r" % body)

    channel.basic_consume(
        queue='hello', on_message_callback=callback, auto_ack=True)

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
