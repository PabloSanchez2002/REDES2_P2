#!/usr/bin/env python
import uuid
import pika
import psycopg2
import sys
import os

ERROR = 0
OK = 1
REGISTERED = 2


class robot(object):
    def __init__(self) -> None:
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))

        self.channel = self.connection.channel()
        self.nombre = None

        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)

        self.corr_id = None

        #self.response = self.connect()
        
        self.connection.close()

    #def connect(self):
    #    os.system('cls' if os.name == 'nt' else 'clear')
    #    self.response = None
    #    self.corr_id = str(uuid.uuid4())
    #    
    #    self.channel.basic_publish(
    #        exchange='',
    #        routing_key='rpc_queue_robot',
    #        properties=pika.BasicProperties(
    #            reply_to=self.callback_queue,
    #            correlation_id=self.corr_id,
    #        ),
    #        body=1
    #    )
    #    while self.response is None:
    #        self.connection.process_data_events()
    #    return self.response
    

    def on_response(self):
        pass

def main():
    contr = robot()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
