"""Pythia: serves the statistics that Hermes keeps in Redis."""

import json
import logging
import logging.config
import os
from contextlib import asynccontextmanager

import connexion
import redis
import yaml
from connexion import request

LOG_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "log_conf.yml")

with open(LOG_CONFIG_PATH, "r") as f:
    log_config = yaml.safe_load(f)

logging.config.dictConfig(log_config)
logger = logging.getLogger("pythia")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
STATS_KEY = "statistics"

# Returned until Hermes has saved its first round, so /stats always answers 200
EMPTY_STATS = {
    "num_distance_events": 0,
    "min_distance": None,
    "max_distance": None,
    "last_updated_distance": None,
    "num_steps_events": 0,
    "min_steps": None,
    "max_steps": None,
    "last_updated_steps": None,
}


@asynccontextmanager
async def lifespan(app):
    # One shared Redis client for the life of the app, instead of one per request
    client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    logger.info("Pythia started: redis=%s", REDIS_URL)
    try:
        yield {"redis": client}  # becomes request.state.redis in the routes
    finally:
        client.close()
        logger.info("Pythia stopped")


# Synchronous on purpose: Connexion runs it in a thread, so the blocking Redis call
# does not stall the event loop.
def get_stats():
    try:
        raw = request.state.redis.get(STATS_KEY)
    except redis.RedisError as e:
        logger.error("Redis unavailable: %s", e)
        return {"message": "statistics store unavailable"}, 503

    if raw is None:
        logger.debug("No statistics saved yet; returning the empty set")
        return dict(EMPTY_STATS), 200

    return {**EMPTY_STATS, **json.loads(raw)}, 200


app = connexion.AsyncApp(__name__, specification_dir="", lifespan=lifespan)
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)