# app/models.py - Полные модели для системы парсинга недвижимости
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    ARRAY, JSON, Float, ForeignKey, Enum, Table,
    UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from databases import Database
from datetime import datetime
import enum

from .config import settings

Base = declarative_base()

# ========================================
# ENUMS
# ========================================

class PropertyType(str, enum.Enum):
    APARTMENT = "apartment"
    HOUSE = "house"
    STUDIO = "studio"
    COMMERCIAL = "commercial"
    LAND = "land"
    OTHER = "other"

class ListingType(str, enum.Enum):
    SALE = "sale"
    RENT = "rent"
    TEMPORARY = "temporary"

class SubscriptionType(str, enum.Enum):
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    PRO = "pro"

class NotificationFrequency(str, enum.Enum):
    IMMEDIATE = "immediate"
    DAILY = "daily"
    WEEKLY = "weekly"

class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    READ = "read"

# ========================================
# ОСНОВНЫЕ МОДЕЛИ
# ========================================

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    language_code = Column(String(10), default='es')
    
    # Подписка
    subscription_type = Column(Enum(SubscriptionType), default=SubscriptionType.FREE)
    subscription_expires_at = Column(DateTime)
    
    # Настройки
    notifications_enabled = Column(Boolean, default=True)
    max_notifications_per_day = Column(Integer, default=10)
    preferred_neighborhoods = Column(ARRAY(String))
    price_range = Column(JSON)  # {"min": 100000, "max": 500000}
    
    # Статистика
    searches_count = Column(Integer, default=0)
    notifications_sent = Column(Integer, default=0)
    last_activity_at = Column(DateTime, default=func.now())
    
    # Мета
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Отношения
    searches = relationship("UserSearch", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("UserFavorite", back_populates="user", cascade="all, delete-orphan")


class Property(Base):
    __tablename__ = "properties"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    
    # Основная информация
    title = Column(String(500), nullable=False)
    description = Column(Text)
    price = Column(Float)
    currency = Column(String(3), default='ARS')
    price_usd = Column(Float)  # Цена в долларах для сравнения
    
    # Характеристики
    property_type = Column(Enum(PropertyType), default=PropertyType.APARTMENT)
    listing_type = Column(Enum(ListingType), default=ListingType.SALE)
    bedrooms = Column(Integer, default=0)
    bathrooms = Column(Integer, default=0)
    area = Column(Float)  # площадь в м²
    
    # Местоположение
    location = Column(String(200))
    neighborhood = Column(String(100))
    address = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Источник
    site = Column(String(50), nullable=False)
    external_id = Column(String(200))  # ID на сайте-источнике
    url = Column(String(1000))
    
    # Медиа
    images = Column(ARRAY(String))  # массив URL изображений
    virtual_tour_url = Column(String(500))
    
    # Дополнительные характеристики
    features = Column(ARRAY(String))  # гараж, терраса, лифт и т.д.
    amenities = Column(ARRAY(String))  # удобства: бассейн, спортзал и т.д.
    floor = Column(String(20))
    total_floors = Column(Integer)
    building_age = Column(Integer)
    
    # Мета-информация
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    views_count = Column(Integer, default=0)
    
    # Временные метки
    first_seen_at = Column(DateTime, default=func.now())
    last_seen_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Для полнотекстового поиска
    search_vector = Column(Text)  # tsvector в PostgreSQL
    
    # Отношения
    notifications = relationship("Notification", back_populates="property")
    favorites = relationship("UserFavorite", back_populates="property")
    price_history = relationship("PriceHistory", back_populates="property", cascade="all, delete-orphan")
    
    # Индексы
    __table_args__ = (
        UniqueConstraint('site', 'external_id', name='_site_external_id_uc'),
        Index('idx_property_search', 'price', 'bedrooms', 'neighborhood', 'property_type'),
        Index('idx_property_created', 'created_at'),
    )


class UserSearch(Base):
    __tablename__ = "user_searches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Информация о поиске
    name = Column(String(200), nullable=False)
    search_criteria = Column(JSON, nullable=False)  # Критерии поиска
    
    # Настройки уведомлений
    notifications_enabled = Column(Boolean, default=True)
    notification_frequency = Column(Enum(NotificationFrequency), default=NotificationFrequency.IMMEDIATE)
    last_notification_sent = Column(DateTime)
    
    # Статистика
    results_count = Column(Integer, default=0)
    notifications_sent = Column(Integer, default=0)
    
    # Мета
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Отношения
    user = relationship("User", back_populates="searches")
    notifications = relationship("Notification", back_populates="search")


class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    property_id = Column(UUID(as_uuid=True), ForeignKey('properties.id'))
    search_id = Column(UUID(as_uuid=True), ForeignKey('user_searches.id'))
    
    # Содержание уведомления
    title = Column(String(200))
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default='new_property')  # new_property, price_change, etc.
    
    # Статус доставки
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING)
    sent_at = Column(DateTime)
    read_at = Column(DateTime)
    error_message = Column(Text)
    
    # Каналы доставки
    telegram_sent = Column(Boolean, default=False)
    email_sent = Column(Boolean, default=False)
    push_sent = Column(Boolean, default=False)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Отношения
    user = relationship("User", back_populates="notifications")
    property = relationship("Property", back_populates="notifications")
    search = relationship("UserSearch", back_populates="notifications")


class UserFavorite(Base):
    __tablename__ = "user_favorites"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    property_id = Column(UUID(as_uuid=True), ForeignKey('properties.id'), nullable=False)
    
    notes = Column(Text)
    rating = Column(Integer)  # 1-5 звёзд
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Отношения
    user = relationship("User", back_populates="favorites")
    property = relationship("Property", back_populates="favorites")
    
    # Уникальное ограничение
    __table_args__ = (
        UniqueConstraint('user_id', 'property_id', name='_user_property_uc'),
    )


class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    property_id = Column(UUID(as_uuid=True), ForeignKey('properties.id'), nullable=False)
    
    old_price = Column(Float)
    new_price = Column(Float)
    old_currency = Column(String(3))
    new_currency = Column(String(3))
    
    change_type = Column(String(20))  # increase, decrease, currency_change
    change_percentage = Column(Float)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Отношения
    property = relationship("Property", back_populates="price_history")


class ScrapingStats(Base):
    __tablename__ = "scraping_stats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    
    site = Column(String(50), nullable=False)
    scraping_date = Column(DateTime, default=func.now())
    
    # Статистика парсинга
    pages_scraped = Column(Integer, default=0)
    properties_found = Column(Integer, default=0)
    properties_new = Column(Integer, default=0)
    properties_updated = Column(Integer, default=0)
    properties_removed = Column(Integer, default=0)
    
    # Производительность
    duration_seconds = Column(Integer)
    errors_count = Column(Integer, default=0)
    success_rate = Column(Float)
    
    # Детали ошибок
    error_details = Column(JSON)
    
    created_at = Column(DateTime, server_default=func.now())


# ========================================
# ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
# ========================================

database = Database(settings.DATABASE_URL)

# Для создания всех таблиц
metadata = Base.metadata
