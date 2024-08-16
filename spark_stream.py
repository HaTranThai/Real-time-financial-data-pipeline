import logging
from cassandra.cluster import Cluster
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType


def create_keyspace(session):
    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS stock_spark_streams
        WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};
    """)
    print("Keyspace created successfully!")

def create_table(session):
    session.execute("""
        CREATE TABLE IF NOT EXISTS stock_spark_streams.data (
            symbol TEXT,
            timestamp TIMESTAMP,
            open DOUBLE,
            high DOUBLE,
            low DOUBLE,
            close DOUBLE,
            volume DOUBLE,
            PRIMARY KEY ((symbol), timestamp)
        );
    """)
    print("Table created successfully!")


def insert_data(session, **kwargs):
    print("Inserting data...")

    symbol = kwargs.get('symbol')
    timestamp = kwargs.get('timestamp')
    open = kwargs.get('open')
    high = kwargs.get('high')
    low = kwargs.get('low')
    close = kwargs.get('close')
    volume = kwargs.get('volume')

    try:
        session.execute("""
            INSERT INTO stock_spark_streams.data (symbol, timestamp, open, high, low, 
                close, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (symbol, timestamp, open, high, low, close, volume))
        logging.info(f"Data inserted for {symbol}")

    except Exception as e:
        logging.error(f'Could not insert data due to: {e}')


def create_spark_connection():
    s_conn = None

    try:
        s_conn = SparkSession.builder \
            .appName('SparkDataStreaming') \
            .config('spark.jars.packages', "com.datastax.spark:spark-cassandra-connector_2.12:3.5.1,"
                                           "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1") \
            .config('spark.cassandra.connection.host', 'localhost') \
            .getOrCreate()

        s_conn.sparkContext.setLogLevel("ERROR")
        logging.info("Spark connection created successfully!")
    except Exception as e:
        logging.error(f"Couldn't create the spark session due to exception {e}")

    return s_conn


def connect_to_kafka(spark_conn):
    spark_df = None
    try:
        spark_df = spark_conn.readStream \
            .format('kafka') \
            .option('kafka.bootstrap.servers', 'localhost:9092') \
            .option('subscribe', 'data') \
            .option('startingOffsets', 'earliest') \
            .option("failOnDataLoss", "false") \
            .load()
        logging.info("kafka dataframe created successfully")
    except Exception as e:
        logging.warning(f"kafka dataframe could not be created because: {e}")

    return spark_df


def create_cassandra_connection():
    try:
        cluster = Cluster(['localhost'])

        cas_session = cluster.connect()

        return cas_session
    except Exception as e:
        logging.error(f"Could not create cassandra connection due to {e}")
        return None


def create_selection_df_from_kafka(spark_df):
    schema = StructType([
        StructField("symbol", StringType(), True),
        StructField("timestamp", StringType(), True),
        StructField("open", StringType(), True),
        StructField("high", StringType(), True),
        StructField("low", StringType(), True),
        StructField("close", StringType(), True),
        StructField("volume", StringType(), True)
    ])

    sel = spark_df.selectExpr("CAST(value AS STRING)") \
        .select(from_json(col('value'), schema).alias('data')).select("data.*")
    print(sel)

    return sel

def delete_checkpoint(checkpoint_dir):
    import shutil
    import os

    if os.path.exists(checkpoint_dir):
        try:
            shutil.rmtree(checkpoint_dir)
            print(f"Checkpoint directory {checkpoint_dir} deleted successfully.")
        except Exception as e:
            print(f"Could not delete checkpoint directory {checkpoint_dir} due to: {e}")
    else:
        print(f"Checkpoint directory {checkpoint_dir} does not exist.")


if __name__ == "__main__":
    # create spark connection
    spark_conn = create_spark_connection()

    if spark_conn is not None:
        # connect to kafka with spark connection
        spark_df = connect_to_kafka(spark_conn)
        selection_df = create_selection_df_from_kafka(spark_df)
        session = create_cassandra_connection()

        if session is not None:
            create_keyspace(session)
            create_table(session)

            logging.info("Streaming is being started...")

            checkpoint_dir = 'path/to/checkpoint/dir'
            delete_checkpoint(checkpoint_dir)

            streaming_query = (selection_df.writeStream
                               .format("org.apache.spark.sql.cassandra")
                               .option('checkpointLocation', checkpoint_dir)
                               .option('keyspace', 'stock_spark_streams')
                               .option('table', 'data')
                               .start())

            streaming_query.awaitTermination()
