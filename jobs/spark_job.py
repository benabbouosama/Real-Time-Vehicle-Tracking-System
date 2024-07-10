import logging
import os
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StringType, DoubleType, IntegerType, TimestampType
from pyspark.sql.functions import from_json, col
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get environment variables
CHECKPOINT_LOCATION = os.getenv("CHECKPOINT_LOCATION")
OUTPUT_PATH = os.getenv("OUTPUT_PATH")

logging.basicConfig(level=logging.INFO)


def read_kafka_topic(spark, topic, schema):
    try:
        return (
            spark.readStream
                .format("kafka")
                .option("kafka.bootstrap.servers", "localhost:9092")
                .option("subscribe", topic)
                .option("startingOffsets", "earliest")
                .load()
                .selectExpr("CAST(value AS STRING)")
                .select(from_json(col("value"), schema).alias("data"))
                .select("data.*")
        )
    except Exception as e:
        logging.error(f"Error reading Kafka topic {topic}: {e}")
        return None

def write_to_gcs(write_df, output_path, checkpoint_location):
    query = (
        write_df.writeStream
            .format("parquet")
            .outputMode("append")
            .option("path", output_path)
            .option("checkpointLocation", checkpoint_location)
            .option("coalesce", "1")
            .start()
    )
    return query

def main():
    try:
        spark = SparkSession.builder.appName("SmartMoroccoStreaming") \
            .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1") \
            .config("spark.hadoop.fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem") \
            .config("spark.hadoop.google.cloud.auth.service.account.enable", "true") \
            .config("spark.hadoop.google.cloud.auth.service.account.json.keyfile", "../keys/keyfile.json") \
            .getOrCreate()

        spark.sparkContext.setLogLevel('WARN')

        vehicule_schema = (
                StructType()
                    .add("id", StringType())
                    .add("deviceId", StringType())
                    .add("timestamp", TimestampType())
                    .add("speed", DoubleType())
                    .add("direction", StringType())
                    .add("make", StringType())
                    .add("model", StringType())
                    .add("year", IntegerType())
            )
        gps_schema = (
                StructType()
                    .add("id", StringType())
                    .add("deviceId", StringType())
                    .add("timestamp", TimestampType())
                    .add("vehicleType", StringType())
                    .add("location", StringType())
            )

        weather_schema = (
                StructType()
                    .add("id", StringType())
                    .add("deviceId", StringType())
                    .add("location", StringType())
                    .add("timestamp", TimestampType())
                    .add("temperature", DoubleType())
                    .add("weatherCondition", StringType())
                    .add("precipitation", DoubleType())
                    .add("humidity", DoubleType())
                    .add("windSpeed", DoubleType())
            )

        # Read data from Kafka topic
        vehicule_df = read_kafka_topic(spark, "vehicle_data", vehicule_schema)
        gps_df = read_kafka_topic(spark, "gps_data", gps_schema)
        weather_df = read_kafka_topic(spark, "weather_data", weather_schema)

        # Write data to GCS bucket (in a csv format)
        if all(df is not None for df in [vehicule_df, gps_df, weather_df]):
            write_to_gcs(vehicule_df, OUTPUT_PATH + "/vehicle_data", CHECKPOINT_LOCATION + "/vehicle_checkpoint")
            write_to_gcs(gps_df, OUTPUT_PATH + "/gps_data", CHECKPOINT_LOCATION + "/gps_checkpoint")
            write_to_gcs(weather_df, OUTPUT_PATH + "/weather_data", CHECKPOINT_LOCATION + "/weather_checkpoint")

            logging.info("Streaming is being started...")
            spark.streams.awaitAnyTermination()
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        spark.stop()

if __name__ == "__main__":
    main()