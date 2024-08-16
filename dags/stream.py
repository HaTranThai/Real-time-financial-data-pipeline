from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import yfinance as yf
import json
from confluent_kafka import Producer

# Configuration parameters for Kafka
KAFKA_BOOTSTRAP_SERVERS = ['broker:29092']
KAFKA_TOPIC = 'data'

symbols = [
    'VHM.VN',  # Vinhomes JSC
    'VIC.VN',  # Vingroup JSC
    'VNM.VN',  # Vinamilk (Vietnam Dairy Products JSC)
    'HPG.VN',  # Hoa Phat Group JSC
    'MSN.VN',  # Masan Group Corp
    'VCB.VN',  # Vietcombank (Joint Stock Commercial Bank for Foreign Trade of Vietnam)
    'BID.VN',  # BIDV (Joint Stock Commercial Bank for Investment and Development of Vietnam)
    'CTG.VN',  # VietinBank (Vietnam Joint Stock Commercial Bank for Industry and Trade)
    'FPT.VN',  # FPT Corporation
    'GAS.VN'   # PetroVietnam Gas JSC
]

# Kafka configuration function
def configure_kafka(servers=KAFKA_BOOTSTRAP_SERVERS):
    settings = {
        'bootstrap.servers': ','.join(servers),
        'client.id': 'producer_instance'
    }
    return Producer(settings)

# Default arguments for DAG
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 7, 15),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(dag_id='streaming_data',
          default_args=default_args,
          schedule_interval='@once',
          catchup=False)

# Function to get data from API
def get_data(ti):
    data = []
    today = datetime.today()
    yesterday = today - timedelta(days=1)
    for symbol in symbols:
        data.append(yf.download(symbol, start='2020-01-01', end=yesterday, interval='1d'))
    ti.xcom_push(key='data', value=data)
    return data

# Function to format data
def format_data(ti):
    formatted_data = []
    data = ti.xcom_pull(task_ids='get_data', key='data')
    for i, symbol in enumerate(symbols):
        for index, row in data[i].iterrows():
            formatted_data.append({
                'symbol': symbol,
                'timestamp': str(index),
                'open': row['Open'],
                'high': row['High'],
                'low': row['Low'],
                'close': row['Close'],
                'volume': row['Volume']
            })
    ti.xcom_push(key='formatted_data', value=formatted_data)
    return formatted_data

# Delivery report callback
def delivery_report(err, msg):
    if err is not None:
        print(f'Delivery failed: {err}')
    else:
        print(f'Delivered message to {msg.topic()} [{msg.partition()}]')

# Function to send data to Kafka
def send_data(ti):
    producer = configure_kafka()
    formatted_data = ti.xcom_pull(task_ids='format_data', key='formatted_data')
    for record in formatted_data:
        producer.produce(KAFKA_TOPIC, json.dumps(record), callback=delivery_report)
    producer.flush()

# Creating tasks
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

send_data_task = PythonOperator(
    task_id='send_data',
    python_callable=send_data,
    dag=dag
)

# Defining task dependencies
get_data_task >> format_data_task >> send_data_task