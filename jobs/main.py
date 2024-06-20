import os
from confluent_kafka import SerializingProducer
import simplejson as json
from datetime import datetime
import random
import requests
import uuid
from datetime import timedelta
import logging
import json
import time
from dotenv import load_dotenv
from uuid import uuid4

load_dotenv()

Fez_Coordinates = {"latitude": 34.0181, "longitude": -5.0078}
Rabat_Coordinates = {"latitude": 34.0084, "longitude": -6.8539}

# Calculate latitude increment (change per step)
LATITUDE_INCREMENT = (Fez_Coordinates["latitude"] - Rabat_Coordinates["latitude"]) / 500

# Calculate longitude increment (change per step)
LONGITUDE_INCREMENT = (
    abs(Fez_Coordinates["longitude"] - Rabat_Coordinates["longitude"]) / 500
)
# Note : Since longitude values are positive for east (and negative for west),
# we should use the absolute value of the difference

# Environment Variables for configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
VEHICLE_TOPIC = os.getenv("VEHICLE_TOPIC", "vehicle_data")
GPS_TOPIC = os.getenv("GPS_TOPIC", "gps_data")
WEATHER_TOPIC = os.getenv("WEATHER_TOPIC", "weather_data")

random.seed(24)

start_time = datetime.now()
start_location = Fez_Coordinates.copy()


def simulate_vehicle_movement():
    global start_location
    # move towards Rabat
    start_location["latitude"] += LATITUDE_INCREMENT
    start_location["longitude"] += LONGITUDE_INCREMENT
    # Add some randomness to simulate reality
    start_location["latitude"] += random.uniform(-0.0007, 0.0004)
    start_location["longitude"] += random.uniform(-0.0007, 0.0004)

    return start_location


def get_next_time():
    global start_time
    start_time += timedelta(seconds=random.randint(30, 60))  # Update frequency
    return start_time


def generate_gps_data(device_id, timestamp, vehicle_type="private"):
    return {
        "id": uuid.uuid4(),
        "deviceId": device_id,
        "timestamp": timestamp,
        "speed": random.uniform(70, 130),
        "Direction": "North-West",
        "vehicleType": vehicle_type,
    }


def generate_vehicle_data(device_id):
    location = simulate_vehicle_movement()
    return {
        "id": str(uuid4()),
        "deviceId": device_id,
        "timestamp": get_next_time().isoformat(),
        "location": (location["latitude"], location["longitude"]),
        "speed": random.uniform(70, 130),
        "direction": "North-West",
        "make": os.getenv("MAKE"),   
        "model": os.getenv("MODEL"),  
        "year": int(os.getenv("YEAR")) 
    }


def get_weather_data(location):
    latitude, longitude = location
    api_key = os.getenv('WEATHER_API_KEY')
    response = requests.get(
        f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={latitude},{longitude}"
    )
    data = response.json()
    return data["current"]


def generate_weather_data(device_id, timestamp, location):
    weather_data = get_weather_data(location)

    return {
        "id": str(uuid.uuid4()),
        "deviceId": device_id,
        "location": {"latitude": location[0], "longitude": location[1]},
        "timestamp": timestamp,
        "temperature": weather_data["temp_c"],
        "weatherCondition": weather_data["condition"]["text"],
        "precipitation": weather_data["precip_mm"],
        "humidity": weather_data["humidity"],
        "windSpeed": weather_data["wind_kph"],
    }


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def json_serializer(obj):
    """Serialize UUID objects to string."""
    if isinstance(obj, uuid.UUID):
        return str(obj)
    raise TypeError(f"Object of Type {obj.__class__.__name__} is not Json Serializable")


def delivery_report(error, message):
    """Callback function to handle message delivery reports."""
    if error is not None:
        logger.error(f"Delivery failed due to: {error}")
    else:
        logger.info(
            f"Message delivered successfully to: {message.topic()} [{message.partition()}]"
        )


def error_callback(exc):
    """Callback function to handle errors in message delivery."""
    # Handle the error as needed
    print(f"Message delivery failed: {exc}")



def produce_data_to_kafka(producer, topic, data):
    """Produce data to Kafka topic."""
    if not producer or not topic or not data:
        raise ValueError("Producer, topic, and data must be provided.")

    # Produce message and specify the acks parameter to handle delivery reports
    producer.produce(
        topic,
        key=str(data["id"]),
        value=json.dumps(data, default=json_serializer).encode("utf-8"),
        on_delivery=delivery_report,
    )

    # Flush the producer to ensure all messages are sent
    producer.flush()  #  Send all messages in the buffer to the Kafka broker immediately


def simulate_journey(producer, device_id):
    while True:
        vehicle_data = generate_vehicle_data(device_id)
        gps_data = generate_gps_data(device_id, vehicle_data["timestamp"])
        weather_data = generate_weather_data(
            device_id, vehicle_data["timestamp"], vehicle_data["location"]
        )

        if (
            vehicle_data["location"][0] >= Rabat_Coordinates["latitude"]
            and vehicle_data["location"][1] <= Rabat_Coordinates["longitude"]
        ):
            print("Rabat reached, simulation ending...")
            break

        produce_data_to_kafka(producer, VEHICLE_TOPIC, vehicle_data)
        produce_data_to_kafka(producer, GPS_TOPIC, gps_data)
        produce_data_to_kafka(producer, WEATHER_TOPIC, weather_data)

        time.sleep(5)

        print(weather_data)


if __name__ == "__main__":

    producer_config = {
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "error_cb": lambda err: print(f"kafka error: {err}"),
    }
    producer = SerializingProducer(producer_config)

    try:
        simulate_journey(producer, "vehicule_moroccan")
    except KeyboardInterrupt:
        print("Simulation ended by the user")
    except Exception as e:
        print(f"Unexpected Error occurred: {e}")
