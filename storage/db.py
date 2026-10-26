import os
import yaml

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

db_url = "mysql://walkr_user:walkr_passwd@localhost/walkr_db"

if db_url.startswith("sqlite:///"):
    db_name = db_url.removeprefix("sqlite:///")
    db_path = os.path.join(os.path.dirname(__file__), db_name)
    db_url = f"sqlite:///{db_path}"

ENGINE = create_engine(db_url)
print("Connecting to:", db_url)
SessionLocal = sessionmaker(bind=ENGINE)

def makeSession():
    return SessionLocal()