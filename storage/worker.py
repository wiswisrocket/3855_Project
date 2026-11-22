"""Storage worker: consumes events from Kafka and saves them to MySQL.

At-least-once delivery: the offset is committed only after the row is saved
(or the message is deliberately skipped), and a unique trace_id turns any
redelivered message into a harmless duplicate.
"""

import json
import logging
import logging.config
import os
import signal
import time
from datetime import datetime

import yaml
from confluent_kafka import Consumer, KafkaException
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from db import ENGINE, makeSession
from models import Base, Distance, Steps

LOG_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "log_conf.yml")

with open(LOG_CONFIG_PATH, "r") as f:
    log_config = yaml.safe_load(f)

logging.config.dictConfig(log_config)
logger = logging.getLogger("worker")

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "redpanda:9092")
KAFKA_TOPIC_1 = os.getenv("KAFKA_TOPIC_1", "distance")
KAFKA_TOPIC_2 = os.getenv("KAFKA_TOPIC_2", "steps")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "storage_worker_group")

MAX_BACKOFF_SECONDS = 30


def build_distance(event):
    return Distance(
        device_id=event["device_id"],
        distance=event["distance"],
        timestamp=datetime.fromisoformat(event["timestamp"]),
        trace_id=event["trace_id"],
    )


def build_steps(event):
    return Steps(
        device_id=event["device_id"],
        steps=event["steps"],
        timestamp=datetime.fromisoformat(event["timestamp"]),
        trace_id=event["trace_id"],
    )


# Which model each topic's messages are saved as
BUILDERS = {
    KAFKA_TOPIC_1: build_distance,
    KAFKA_TOPIC_2: build_steps,
}


def handle_sigterm(signum, frame):
    # `docker stop` sends SIGTERM: treat it like Ctrl-C so the finally block closes the consumer
    raise KeyboardInterrupt


def wait_for_database():
    """Create the tables, retrying while MySQL is unreachable."""
    delay = 1
    while True:
        try:
            Base.metadata.create_all(ENGINE)
            logger.info("Database ready")
            return
        except OperationalError as e:
            logger.warning("Database unavailable at startup (%s), retrying in %ss", e.orig, delay)
            time.sleep(delay)
            delay = min(delay * 2, MAX_BACKOFF_SECONDS)


def save_event(row):
    """Save one row, retrying while the database is down.

    Returns once the row is stored or confirmed to be a duplicate. While MySQL is
    down this keeps retrying the SAME message, so the worker stops consuming and
    its Kafka offset stays where it was.
    """
    delay = 1
    while True:
        with makeSession() as session:
            try:
                session.add(row)
                session.commit()
                return "stored"
            except IntegrityError:
                # trace_id is unique: this message was already saved (redelivery)
                session.rollback()
                return "duplicate"
            except OperationalError as e:
                session.rollback()
                logger.warning(
                    "Database unavailable (%s), retrying trace_id %s in %ss",
                    e.orig, row.trace_id, delay,
                )
        time.sleep(delay)
        delay = min(delay * 2, MAX_BACKOFF_SECONDS)


def commit_offset(consumer, msg):
    try:
        consumer.commit(message=msg, asynchronous=False)
    except KafkaException as e:
        # e.g. the group rebalanced during a long database outage: the message will
        # be delivered again, and the unique trace_id makes the second save a no-op
        logger.warning("Offset commit failed (%s); message may be redelivered", e)


def process_message(consumer, msg):
    topic = msg.topic()
    builder = BUILDERS.get(topic)

    if builder is None:
        logger.warning("Message from unexpected topic '%s', skipping", topic)
        commit_offset(consumer, msg)
        return

    try:
        event = json.loads(msg.value().decode("utf-8"))
        row = builder(event)
    except (ValueError, UnicodeDecodeError, KeyError, TypeError) as e:
        # Bad JSON or missing/invalid fields: retrying would never succeed, so skip it
        logger.error("Malformed message on %s at offset %d (%s), skipping", topic, msg.offset(), e)
        commit_offset(consumer, msg)
        return

    try:
        result = save_event(row)
    except SQLAlchemyError:
        # Not a connection problem (e.g. invalid data for a column): skipping is the only way forward
        logger.exception("Permanent database error on %s at offset %d, skipping", topic, msg.offset())
        commit_offset(consumer, msg)
        return

    if result == "duplicate":
        logger.info("Duplicate %s event, trace_id %s already stored", topic, event["trace_id"])
    else:
        logger.info("Stored %s event, trace_id %s", topic, event["trace_id"])

    commit_offset(consumer, msg)


def main():
    signal.signal(signal.SIGTERM, handle_sigterm)

    wait_for_database()

    config = {
        "bootstrap.servers": KAFKA_BROKER,
        "group.id": KAFKA_GROUP_ID,
        # A new group starts from the oldest message instead of only new ones
        "auto.offset.reset": "earliest",
        # Commit manually, only after the database save
        "enable.auto.commit": False,
    }

    consumer = Consumer(config)
    try:
        consumer.subscribe([KAFKA_TOPIC_1, KAFKA_TOPIC_2])
        logger.info("Worker started: broker=%s topics=%s,%s group=%s",
                    KAFKA_BROKER, KAFKA_TOPIC_1, KAFKA_TOPIC_2, KAFKA_GROUP_ID)

        while True:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue  # nothing new within the timeout

            if msg.error():
                if msg.error().fatal():
                    raise KafkaException(msg.error())
                # Non-fatal (e.g. broker briefly unreachable): confluent_kafka retries on its own
                logger.warning("Kafka error: %s", msg.error())
                continue

            process_message(consumer, msg)

    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
    finally:
        logger.info("Closing Kafka connection...")
        consumer.close()


if __name__ == "__main__":
    main()