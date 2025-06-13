from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ARRAY, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from databases import Database

from .config import settings

Base = declarative_base()

class Property(Base):
    __tablename__ = "properties"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    external_id = Column(String, index=True)
    source = Column(String)
    url = Column(String)
    neighborhood = Column(String)
    price_usd = Column(Float)
    price_ars = Column(Float)
    rooms = Column(Integer)
    area = Column(Float)
    address = Column(String)
    floor = Column(String)
    elevator = Column(Boolean)
    parking = Column(Boolean)
    balcony = Column(Boolean)
    terrace = Column(Boolean)
    furnished = Column(Boolean)
    phone = Column(String)
    description = Column(Text)
    photos = Column(ARRAY(String))
    published_at = Column(DateTime)
    scraped_at = Column(DateTime)
    status = Column(String)
    hash = Column(String)
    first_seen_at = Column(DateTime)
    last_updated_at = Column(DateTime)
    price_changes = Column(JSON)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

database = Database(settings.DATABASE_URL)
