import functools
import connexion
from connexion import NoContent

from db import makeSession
from models import Distance, Steps


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
        timestamp = body["timestamp"]
    )

    session.add(event)
    session.commit()

    print("Recorded distance: ", body)
    return NoContent, 201

@use_db_session
def record_steps(session, body):
    event = Steps(
        device_id = body["device_id"],
        steps = body["steps"],
        timestamp = body["timestamp"]
    )
    
    session.add(event)
    session.commit()

    print("Recorded steps: ", body)
    return NoContent, 201

app = connexion.AsyncApp(__name__, specification_dir='')
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)