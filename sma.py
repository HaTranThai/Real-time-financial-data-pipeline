import pandas as pd
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement, BatchStatement
from datetime import datetime

cluster = Cluster(['localhost'])
session = cluster.connect()

session.execute("USE stock_spark_streams")

today = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

start_date = '2020-01-01T00:00:00Z'

symbols = [
    'VHM.VN', 'VIC.VN', 'VNM.VN', 'HPG.VN', 'MSN.VN', 'VCB.VN', 'BID.VN', 'CTG.VN', 'FPT.VN', 'GAS.VN'
]

session.execute("""
    CREATE TABLE IF NOT EXISTS sma (
        timestamp TIMESTAMP,
        symbol TEXT,
        sma_7 DOUBLE,
        sma_30 DOUBLE,
        sma_60 DOUBLE,
        PRIMARY KEY ((symbol), timestamp)
    )
""")

for symbol in symbols:
    query = f"""
    SELECT * FROM stock_spark_streams.data
    WHERE symbol = '{symbol}'
    AND timestamp >= '{start_date}'
    AND timestamp <= '{today}'
    ALLOW FILTERING
    """
    rows = session.execute(query)
    df = pd.DataFrame(rows)

    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        df['sma_7'] = df.groupby('symbol')['close'].transform(lambda x: x.rolling(window=7).mean())
        df['sma_30'] = df.groupby('symbol')['close'].transform(lambda x: x.rolling(window=30).mean())
        df['sma_60'] = df.groupby('symbol')['close'].transform(lambda x: x.rolling(window=60).mean())

        df = df.fillna({'sma_7': 0, 'sma_30': 0, 'sma_60': 0})

        batch = BatchStatement()

        for _, row in df.iterrows():
            timestamp = row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            statement = SimpleStatement("""
            INSERT INTO sma (timestamp, symbol, sma_7, sma_30, sma_60)
            VALUES (%s, %s, %s, %s, %s)
            """)
            batch.add(statement, (timestamp, row['symbol'], row['sma_7'], row['sma_30'], row['sma_60']))

        try:
            session.execute(batch)
            print(f"SMA calculation and insertion completed for symbol: {symbol}.")
        except Exception as e:
            print(f"An error occurred for symbol {symbol}: {e}")

# Đóng kết nối
cluster.shutdown()
