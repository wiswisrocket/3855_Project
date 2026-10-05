from datetime import datetime, UTC
from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy import Integer, String, DateTime, Float


class Base(DeclarativeBase):
    pass

class Distance(Base):
    __tablename__ = "distance"
    id = mapped_column(Integer, primary_key=True)
    device_id = mapped_column(String(50), nullable=False)
    distance = mapped_column(Float, nullable=False)
    timestamp = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    recorded_timestamp = mapped_column(DateTime, default=lambda: datetime.now(UTC))

class Steps(Base):
    __tablename__ = "steps"
    id = mapped_column(Integer, primary_key=True)
    device_id = mapped_column(String(50), nullable=False)
    steps = mapped_column(Integer, nullable=False)
    timestamp = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    recorded_timestamp = mapped_column(DateTime, default=lambda: datetime.now(UTC))