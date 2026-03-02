from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class MarketStatus(str, enum.Enum):
    ACTIVE = "Active"
    PENDING = "Pending"
    SOLD = "Sold"


class WorkflowStatus(str, enum.Enum):
    NEW = "New"
    CALL = "Call"
    FOLLOW_UP = "Follow Up"
    SKIP = "Skip"


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String(255), nullable=False, index=True)
    city = Column(String(100))
    zip_code = Column(String(10), index=True)
    neighborhood = Column(String(255))

    price = Column(Integer)  # Price in cents
    beds = Column(Integer)
    baths = Column(Float)
    sqft = Column(Integer)
    price_per_sqft = Column(Integer)  # In cents
    days_on_market = Column(Integer)

    market_status = Column(Enum(MarketStatus), default=MarketStatus.ACTIVE)
    workflow_status = Column(Enum(WorkflowStatus), default=WorkflowStatus.NEW)
    follow_up_date = Column(Date, nullable=True)

    redfin_url = Column(String(512))

    # Agent info (user-entered)
    agent_name = Column(String(255), nullable=True)
    agent_phone = Column(String(50), nullable=True)

    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    price_history = relationship("PriceHistory", back_populates="property", cascade="all, delete-orphan")
    status_history = relationship("StatusHistory", back_populates="property", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="property", cascade="all, delete-orphan")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    price = Column(Integer, nullable=False)  # In cents
    recorded_at = Column(DateTime, default=datetime.utcnow)

    property = relationship("Property", back_populates="price_history")


class StatusHistory(Base):
    __tablename__ = "status_history"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    from_status = Column(String(50))
    to_status = Column(String(50))
    changed_at = Column(DateTime, default=datetime.utcnow)
    source = Column(String(20))  # 'user' or 'import'

    property = relationship("Property", back_populates="status_history")


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    property = relationship("Property", back_populates="notes")
