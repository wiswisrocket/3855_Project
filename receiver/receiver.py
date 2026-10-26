import json
import os
import requests
import time
import yaml
import logging
import logging.config

import connexion
from connexion import NoContent

LOG_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "log_conf.yml")

with open(LOG_CONFIG_PATH, "r") as f:
    log_config = yaml.safe_load(f)

logging.config.dictConfig(log_config)
logger = logging.getLogger("receiver")


STORAGE = os.getenv("STORAGE_SERVICE_URL", "http://localhost:8090")

def report_distance(body):
    body["trace_id"] = time.time_ns()
    logger.info(f"Received 'distance' event - distance: {body['distance']} | trace_id:{body['trace_id']}")

    r = requests.post(f"{STORAGE}/events/distance", json=body)
    logger.debug(f"Response for event distance (id: {body['trace_id']}) has status {r.status_code}")

    return r.text, r.status_code

def report_steps(body):
    body["trace_id"] = time.time_ns()
    logger.info(f"Received 'steps' event - steps: {body['steps']} | trace_id:{body['trace_id']}")

    r = requests.post(f"{STORAGE}/events/steps", json=body)
    logger.debug(f"Response for event steps (id: {body['trace_id']}) has status {r.status_code}")

    return r.text, r.status_code

def get_status():
    return {"status": "ok"}, 200

app = connexion.AsyncApp(__name__, specification_dir='')
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)

