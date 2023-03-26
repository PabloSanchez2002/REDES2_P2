import pika
import uuid

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

result = channel.queue_declare(queue='', exclusive=True)
callback_queue = result.method.queue


def rpc_response_callback(ch, method, props, body):
    if corr_id == props.correlation_id:
        response = body
        print("RPC response:", response)


channel.basic_consume(queue=callback_queue, on_message_callback=rpc_response_callback, auto_ack=True)


message = "Hello, World!"
corr_id = str(uuid.uuid4())
channel.basic_publish(exchange='',
                      routing_key='rpc_queue',
                      properties=pika.BasicProperties(reply_to=callback_queue, correlation_id=corr_id),
                      body=message)

print("RPC request sent:", message)
while True:
    connection.process_data_events()