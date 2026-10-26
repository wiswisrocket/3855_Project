import os
import yaml

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

db_url = os.getenv("DATABASE_URL", "mysql://walkr_user:walkr_passwd@localhost/walkr_db")

ENGINE = create_engine(db_url)
SessionLocal = sessionmaker(bind=ENGINE)

def makeSession():
    return SessionLocal()