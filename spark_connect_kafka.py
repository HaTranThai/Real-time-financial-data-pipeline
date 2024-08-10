from pyspark.sql import SparkSession
from pyspark.sql.functions import expr

spark = SparkSession.builder \
    .appName("Spark-Kafka-Example") \
    .config('spark.jars.packages', "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1") \
    .getOrCreate()

df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "stock_data") \
    .load()

from pyspark.sql.types import StructType, StructField, StringType
from pyspark.sql.functions import from_json, col

df = df.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)")
schema = StructType([
        StructField("symbol", StringType(), True),
        StructField("timestamp", StringType(), True),
        StructField("open", StringType(), True),
        StructField("high", StringType(), True),
        StructField("low", StringType(), True),
        StructField("close", StringType(), True),
        StructField("volume", StringType(), True)
    ])

sel = df.selectExpr("CAST(value AS STRING)") \
        .select(from_json(col('value'), schema).alias('data')).select("data.*")

query = sel \
    .writeStream \
    .outputMode("append") \
    .format("console") \
    .start()

query.awaitTermination()
