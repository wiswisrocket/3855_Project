import os
import time
import logging

from models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)

db_url = os.getenv("DATABASE_URL", "mysql://walkr_user:walkr_passwd@localhost/walkr_db")

ENGINE = create_engine(db_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=ENGINE)

def makeSession():
    return SessionLocal()


MAX_BACKOFF_SECONDS = 30

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