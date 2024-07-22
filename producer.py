import json
from kafka import KafkaProducer
import finnhub
from datetime import datetime
from data_generator import generate_message
import time

def serializer(message):
    return json.dumps(message).encode('utf-8')

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=serializer
)

finnhub_client = finnhub.Client(api_key="cqchq4pr01qoodgbgkbgcqchq4pr01qoodgbgkc0")

quote_data = finnhub_client.quote('AAPL')

message = {
    'symbol': 'AAPL',
    'data': quote_data,
    'timestamp': datetime.utcnow().isoformat()
}

producer.send('finnhub', message)
producer.flush()

print("Message sent:", message)