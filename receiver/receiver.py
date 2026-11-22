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
from aiokafka.errors import KafkaConnectionError, KafkaError
import asyncio

LOG_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "log_conf.yml")

with open(LOG_CONFIG_PATH, "r") as f:
    log_config = yaml.safe_load(f)

logging.config.dictConfig(log_config)
logger = logging.getLogger("receiver")


KAFKA_BROKER = os.getenv("KAFKA_BROKER", "redpanda:9092")
KAFKA_TOPIC_1 = os.getenv("KAFKA_TOPIC_1", "distance")
KAFKA_TOPIC_2 = os.getenv("KAFKA_TOPIC_2", "steps")


async def start_producer():
    delay = 1
    while True:
        producer = AIOKafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            enable_idempotence=True,
            request_timeout_ms=10_000,
            retry_backoff_ms=250,
            linger_ms=5
        )

        try:
            await producer.start()
            return producer
        except KafkaConnectionError:
            # Cannot connect: backoff and retry
            logger.warning(f"Kafka not reachable, retrying ins {delay}")
            await producer.stop()
            await asyncio.sleep(delay)
            # Max delay =30s
            delay = min(delay * 2, 30)


@asynccontextmanager
async def lifespan(app):
    producer = await start_producer()
    try:
        yield {"kafka": producer}
    finally:
        await producer.stop()


async def report_distance(body):
    data = {**body, "trace_id": time.time_ns()}
    logger.info(f"Received 'distance' event - distance: {data['distance']} | trace_id:{data['trace_id']}")
    payload = json.dumps(data).encode("utf-8")

    try:
        await asyncio.wait_for(
            request.state.kafka.send_and_wait(KAFKA_TOPIC_1, payload), timeout=5
        )
    except (KafkaError, asyncio.TimeoutError):
        logger.warning(f"Kafka unavailable, rejected 'distance' event | trace_id: {data["trace_id"]}")
        return {"message": "temporarily unavailable"}, 503

    logger.info(f"Produced 'distance' event | distance: {data["distance"]} | trace_id: {data["trace_id"]}")
    return NoContent, 201

async def report_steps(body):
    data = {**body, "trace_id": time.time_ns()}
    logger.info(f"Received 'steps' event - steps: {data['steps']} | trace_id:{data['trace_id']}")
    payload = json.dumps(data).encode("utf-8")

    try:
        await asyncio.wait_for(
            request.state.kafka.send_and_wait(KAFKA_TOPIC_2, payload), timeout=5
        )
    except (KafkaError, asyncio.TimeoutError):
        logger.warning(f"Kafka unavailable, rejected 'steps' event | trace_id: {data["trace_id"]}")
        return {"message": "temporarily unavailable"}, 503

    logger.info(f"Produced 'steps' event | steps: {data["steps"]} | trace_id: {data["trace_id"]}")
    return NoContent, 201


def get_status():
    return {"status": "ok"}, 200


app = connexion.AsyncApp(__name__, specification_dir='', lifespan=lifespan)
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)

