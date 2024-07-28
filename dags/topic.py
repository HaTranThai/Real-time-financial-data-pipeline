# Import các thư viện cần thiết
import finnhub
import json
from datetime import datetime
from kafka import KafkaProducer
from airflow import DAG
from airflow.operators.python import PythonOperator
import logging
from confluent_kafka import Producer

# Cấu hình các tham số cho Kafka
KAFKA_BOOTSTRAP_SERVERS = ['broker:29092']
KAFKA_TOPIC = "topic_finnhub"
PAUSE_INTERVAL = 10
STREAMING_DURATION = 120

# Hàm cấu hình Kafka
def configure_kafka(servers=KAFKA_BOOTSTRAP_SERVERS):
    settings = {
        'bootstrap.servers': ','.join(servers),
        'client.id': 'producer_instance'  
    }
    return Producer(settings)

# Hàm kiểm tra trạng thái gửi message
def delivery_status(err, msg):
    if err is not None:
        print('Gửi thất bại:', err)
    else:
        print('Message được gửi tới', msg.topic(), '[Partition: {}]'.format(msg.partition()))

# Hàm gửi message tới Kafka
def publish_to_kafka(producer, topic, data):
    producer.produce(topic, value=json.dumps(data).encode('utf-8'), callback=delivery_status)
    producer.flush()

# Hàm lấy dữ liệu từ API và gửi tới Kafka
def stream_data():
    finnhub_client = finnhub.Client(api_key="cqchq4pr01qoodgbgkbgcqchq4pr01qoodgbgkc0")

    quote_data = finnhub_client.quote('AAPL')

    message = {
        'symbol': 'AAPL',
        'data': quote_data,
        'timestamp': datetime.now().isoformat()
    }

    print(message)
    
    producer = configure_kafka()

    publish_to_kafka(producer, KAFKA_TOPIC, message)

# Cấu hình DAG
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 1, 10, 00)
}

# Tạo DAG
with DAG('finnhub_kafka',
         default_args=default_args,
         schedule_interval='* * * * *',
         catchup=False) as dag:

    streaming_task = PythonOperator(
        task_id='stream_data_from_api',
        python_callable=stream_data
    )

# Kết nối các task trong DAG
streaming_task

