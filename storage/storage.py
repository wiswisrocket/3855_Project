import functools
import connexion
from connexion import NoContent
import os
import yaml
import logging
import logging.config

from db import makeSession
from models import Distance, Steps

from datetime import datetime

LOG_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "log_conf.yml")

with open(LOG_CONFIG_PATH, "r") as f:
    log_config = yaml.safe_load(f)

logging.config.dictConfig(log_config)
logger = logging.getLogger("storage")


def use_db_session(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        session = makeSession()
        try:
            return func(session, *args, **kwargs)
        finally:
            session.close()

    return wrapper

@use_db_session
def record_distance(session, body):
    event = Distance(
        device_id = body["device_id"],
        distance = body["distance"],
        timestamp = datetime.fromisoformat(body["timestamp"]),
        trace_id = body["trace_id"]
    )

    session.add(event)
    session.commit()
    logger.debug(f"Stored event 'distance' with a trace id of {body['trace_id']}")

    print("Recorded distance: ", body)
    return NoContent, 201

@use_db_session
def record_steps(session, body):
    event = Steps(
        device_id = body["device_id"],
        steps = body["steps"],
        timestamp = datetime.fromisoformat(body["timestamp"]),
        trace_id = body["trace_id"]
    )
    
    session.add(event)
    session.commit()
    logger.debug(f"Stored event 'steps' with a trace id of {body['trace_id']}")

    print("Recorded steps: ", body)
    return NoContent, 201

app = connexion.AsyncApp(__name__, specification_dir='')
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)