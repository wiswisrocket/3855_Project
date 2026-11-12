import json
import os
import requests
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


STORAGE = os.getenv("STORAGE_SERVICE_URL", "http://localhost:8090")

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "http://redpanda:9092")
KAFKA_TOPIC_1 = os.getenv("KAFKA_TOPIC_1", "distance")

@asynccontextmanager
async def lifespan(app):
    producer = AIOKafkaProducer(bootstrap_servers=[KAFKA_BROKER])

    await producer.start()
    try:
        yield {"kafka": producer}
    finally:
        await producer.stop()

async def report_distance(body):
    # body["trace_id"] = time.time_ns()
    # logger.info(f"Received 'distance' event - distance: {body['distance']} | trace_id:{body['trace_id']}")

    # r = requests.post(f"{STORAGE}/events/distance", json=body)
    # logger.debug(f"Response for event distance (id: {body['trace_id']}) has status {r.status_code}")

    # return r.text, r.status_code

    data = {**body, "trace_id": time.time_ns()}
    payload = json.dumps(data)

    await request.state.kafka.send(KAFKA_TOPIC_1, payload.encode("utf-8"))

    return NoContent, 201

def report_steps(body):
    body["trace_id"] = time.time_ns()
    logger.info(f"Received 'steps' event - steps: {body['steps']} | trace_id:{body['trace_id']}")

    r = requests.post(f"{STORAGE}/events/steps", json=body)
    logger.debug(f"Response for event steps (id: {body['trace_id']}) has status {r.status_code}")

    return r.text, r.status_code

def get_status():
    return {"status": "ok"}, 200

app = connexion.AsyncApp(__name__, specification_dir='', lifespan=lifespan)
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)

