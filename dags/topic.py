# Import các thư viện cần thiết
import finnhub
import json
from datetime import datetime
from kafka import KafkaProducer
from airflow import DAG
from airflow.operators.python import PythonOperator
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


# Hàm lấy dữ liệu từ Finnhub
def get_data():
    finnhub_client = finnhub.Client(api_key="cqchq4pr01qoodgbgkbgcqchq4pr01qoodgbgkc0")
    quote_data = finnhub_client.quote('AAPL')
    return quote_data

# Hàm format dữ liệu
def format_data(ti):
    quote_data = ti.xcom_pull(task_ids='get_data')
    message = {
        'symbol': 'AAPL',
        'date_time': datetime.fromtimestamp(quote_data['t']).strftime('%d/%m/%Y, %H:%M:%S'),
        'open': quote_data['o'],
        'high': quote_data['h'],
        'low': quote_data['l'],
        'current_price': quote_data['c'],
        'previous_close': quote_data['pc'],
        'change_percent': quote_data['dp']
    }
    return message


# Hàm kiểm tra trạng thái gửi message
def delivery_status(err, msg):
    if err is not None:
        print('Gửi thất bại:', err)
    else:
        print('Message được gửi tới', msg.topic(), '[Partition: {}]'.format(msg.partition()))


# Hàm gửi message tới Kafka
def stream_data(ti):
    producer = configure_kafka()
    formatted_data = ti.xcom_pull(task_ids='format_data')
    message = json.dumps(formatted_data).encode('utf-8')
    try:
        producer.produce(KAFKA_TOPIC, message, callback=delivery_status)
        producer.flush()
    except Exception as e:
        print(f"Lỗi : {e}")

# Cấu hình DAG
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 1, 10, 00)
}

dag = DAG(
    'finnhub_data_streaming',
    default_args=default_args,
    description='DAG for streaming data from Finnhub to Kafka',
    schedule_interval='@once',
)

# Tạo task
get_data_task = PythonOperator(
    task_id='get_data',
    python_callable=get_data,
    dag=dag
)

format_data_task = PythonOperator(
    task_id='format_data',
    python_callable=format_data,
    dag=dag
)

streaming_task = PythonOperator(
    task_id='stream_data',
    python_callable=stream_data,
    dag=dag
)

# Kết nối các task trong DAG
get_data_task >> format_data_task >> streaming_task

