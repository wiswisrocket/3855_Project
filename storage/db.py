import os
import yaml

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


CONFIG_PATH = os.path.join(os.path.dirname(__file__), "app_conf.yml")
with open(CONFIG_PATH, "r") as f:
    app_config = yaml.safe_load(f)

db_url = app_config["datastore"]["url"]

if db_url.startswith("sqlite:///"):
    db_name = db_url.removeprefix("sqlite:///")
    db_path = os.path.join(os.path.dirname(__file__), db_name)
    db_url = f"sqlite///{db_path}"

ENGINE = create_engine(db_url)

def makeSession():
    return sessionmaker(bind=ENGINE)