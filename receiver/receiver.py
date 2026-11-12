import json
import os
import time
import yaml
import logging
import logging.config

import connexion
from connexion import NoContent, request

from contextlib import asynccontextmanager
from aiokafka import AIOKafkaProducer

LOG_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "log_conf.yml")

with open(LOG_CONFIG_PATH, "r") as f:
    log_config = yaml.safe_load(f)

logging.config.dictConfig(log_config)
logger = logging.getLogger("receiver")


KAFKA_BROKER = os.getenv("KAFKA_BROKER", "redpanda:9092")
KAFKA_TOPIC_1 = os.getenv("KAFKA_TOPIC_1", "distance")
KAFKA_TOPIC_2 = os.getenv("KAFKA_TOPIC_2", "steps")

@asynccontextmanager
async def lifespan(app):
    producer = AIOKafkaProducer(bootstrap_servers=[KAFKA_BROKER])

    await producer.start()
    try:
        yield {"kafka": producer}
    finally:
        await producer.stop()

async def report_distance(body):
    data = {**body, "trace_id": time.time_ns()}
    logger.info(f"Received 'distance' event - distance: {data['distance']} | trace_id:{data['trace_id']}")
    payload = json.dumps(data)

    await request.state.kafka.send(KAFKA_TOPIC_1, payload.encode("utf-8"))

    return NoContent, 201

async def report_steps(body):
    data = {**body, "trace_id": time.time_ns()}
    logger.info(f"Received 'steps' event - steps: {data['steps']} | trace_id:{data['trace_id']}")
    payload = json.dumps(data)

    await request.state.kafka.send(KAFKA_TOPIC_2, payload.encode("utf-8"))

    return NoContent, 201

def get_status():
    return {"status": "ok"}, 200

app = connexion.AsyncApp(__name__, specification_dir='', lifespan=lifespan)
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)

