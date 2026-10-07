import json
import os
import requests

import yaml

import connexion
from connexion import NoContent

# Load app config (project root, one level up from receiver/)
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "app_conf.yml")
with open(CONFIG_PATH, "r") as f:
    app_config = yaml.safe_load(f)

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", app_config["datastore"]["filename"])


def _load_data():
    """Load the events data file, creating a default structure if it doesn't exist yet."""
    if not os.path.exists(DATA_FILE):
        return {
            "events": [],
            "counts": {
                "distance": 0,
                "steps": 0
            }
        }

    with open(DATA_FILE, "r") as f:
        return json.load(f)


def _save_data(data):
    """Write the events data back to disk."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _record_event(event_type, body):
    """Append a new event of the given type and bump its counter."""
    data = _load_data()

    data["events"].append({
        "type": event_type,
        "data": body
    })
    data["counts"][event_type] = data["counts"].get(event_type, 0) + 1

    _save_data(data)


def report_distance(body):
    print("Received distance event: ", body)
    
    _record_event("distance", body)
    return NoContent, 201



def report_steps(body):
    print("Received steps event: ", body)

    _record_event("steps", body)
    return NoContent, 201


app = connexion.AsyncApp(__name__, specification_dir='')
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)

