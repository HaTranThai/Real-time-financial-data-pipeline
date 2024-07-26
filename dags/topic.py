import finnhub
import json
from datetime import datetime
from kafka import KafkaProducer
from airflow import DAG
from airflow.operators.python import PythonOperator
import logging
from confluent_kafka import Producer

KAFKA_BOOTSTRAP_SERVERS = ['broker:29092']
KAFKA_TOPIC = "topic_finnhub"
PAUSE_INTERVAL = 10
STREAMING_DURATION = 120

def configure_kafka(servers=KAFKA_BOOTSTRAP_SERVERS):
    settings = {
        'bootstrap.servers': ','.join(servers),
        'client.id': 'producer_instance'  
    }
    return Producer(settings)

def delivery_status(err, msg):
    if err is not None:
        print('Gửi thất bại:', err)
    else:
        print('Message được gửi tới', msg.topic(), '[Partition: {}]'.format(msg.partition()))

def publish_to_kafka(producer, topic, data):
    producer.produce(topic, value=json.dumps(data).encode('utf-8'), callback=delivery_status)
    producer.flush()

def stream_data():
    finnhub_client = finnhub.Client(api_key="cqchq4pr01qoodgbgkbgcqchq4pr01qoodgbgkc0")

    quote_data = finnhub_client.quote('AAPL')

    message = {
        'symbol': 'AAPL',
        'data': quote_data,
        'timestamp': datetime.utcnow().isoformat()
    }

    print(message)
    
    producer = configure_kafka()

    publish_to_kafka(producer, KAFKA_TOPIC, message)

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 1, 10, 00)
}

with DAG('finnhub_kafka',
         default_args=default_args,
         schedule_interval='@once',
         catchup=False) as dag:

    streaming_task = PythonOperator(
        task_id='stream_data_from_api',
        python_callable=stream_data
    )

streaming_task

