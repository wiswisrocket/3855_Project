from datetime import datetime, UTC
from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy import Integer, String, Float, BigInteger
from sqlalchemy.dialects.mysql import TIMESTAMP


class Base(DeclarativeBase):
    pass

class Distance(Base):
    __tablename__ = "distance"
    id = mapped_column(Integer, primary_key=True)
    device_id = mapped_column(String(50), nullable=False)
    distance = mapped_column(Float, nullable=False)
    timestamp = mapped_column(TIMESTAMP(fsp=6), default=lambda: datetime.now(UTC))
    recorded_timestamp = mapped_column(TIMESTAMP(fsp=6), default=lambda: datetime.now(UTC))
    trace_id = mapped_column(BigInteger)

class Steps(Base):
    __tablename__ = "steps"
    id = mapped_column(Integer, primary_key=True)
    device_id = mapped_column(String(50), nullable=False)
    steps = mapped_column(Integer, nullable=False)
    timestamp = mapped_column(TIMESTAMP(fsp=6), default=lambda: datetime.now(UTC))
    recorded_timestamp = mapped_column(TIMESTAMP(fsp=6), default=lambda: datetime.now(UTC))
    trace_id = mapped_column(BigInteger)

def to_json(self):
    return {
        "device_id": self.device_id,
        "distance": self.distance,
        "timestamp": self.timestamp.isoformat(),
        "trace_id": self.trace_id,
    }