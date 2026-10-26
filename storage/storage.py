import functools
import connexion
from connexion import NoContent
import os
import yaml
import logging
import logging.config

from db import makeSession, ENGINE
from models import Distance, Steps, Base
from sqlalchemy import select, func

from datetime import datetime

LOG_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "log_conf.yml")

with open(LOG_CONFIG_PATH, "r") as f:
    log_config = yaml.safe_load(f)

logging.config.dictConfig(log_config)
logger = logging.getLogger("storage")

# A fresh MySQL container has no tables; create_all skips tables that already exist
Base.metadata.create_all(ENGINE)


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


@use_db_session
def get_distance_reports(session, after=None):
    query = select(Distance)

    if after:
        try:
            cutoff = datetime.fromisoformat(after)
        except ValueError:
            logger.warning(f"Rejected distance request: invalid 'after' value {after!r}")
            return {"message": f"Invalid timestamp: {after}"}, 400
        query = query.where(Distance.recorded_timestamp > cutoff)

    query = query.order_by(Distance.recorded_timestamp)
    reports = session.scalars(query).all()

    logger.debug(f"Found {len(reports)} distance reports after {after}.")

    return [r.to_json() for r in reports], 200

@use_db_session
def get_steps_reports(session, after=None):
    query = select(Steps)

    if after:
        try:
            cutoff = datetime.fromisoformat(after)
        except ValueError:
            logger.warning(f"Rejected steps request: invalid 'after' value {after!r}")
            return {"message": f"Invalid timestamp: {after}"}, 400
        query = query.where(Steps.recorded_timestamp > cutoff)

    query = query.order_by(Steps.recorded_timestamp)
    reports = session.scalars(query).all()

    logger.debug(f"Found {len(reports)} steps reports after {after}.")

    return [r.to_json() for r in reports], 200


@use_db_session
def get_status(session):
    distance_count = session.execute(select(func.count()).select_from(Distance)).scalar()
    steps_count = session.execute(select(func.count()).select_from(Steps)).scalar()

    return {"status": "ok",
            "distance_count": distance_count,
            "steps_count": steps_count
            }, 200

def reset_db():
    Base.metadata.drop_all(ENGINE)
    print("Tables dropped!")

    Base.metadata.create_all(ENGINE)
    print("Tables created!")

    return {"message": "database reset"}, 200

app = connexion.AsyncApp(__name__, specification_dir='')

app.add_api("openapi.yml", strict_validation=True, validate_responses=True)