# app/config.py - Полная конфигурация системы
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Общие настройки
    APP_NAME: str = "Property Scraper"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    
    # Настройки базы данных
    DATABASE_URL: str = "postgresql://scraper:scraper123@postgres:5432/property_scraper"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Настройки Redis
    REDIS_URL: str = "redis://redis:6379"
    REDIS_CACHE_TTL: int = 3600  # 1 час
    
    # Настройки Crawl4AI
    CRAWL4AI_URL: str = "http://crawl4ai:11235"
    CRAWL4AI_API_TOKEN: Optional[str] = None
    
    # Настройки Ollama
    OLLAMA_URL: str = "http://ollama:11434"
    AI_MODEL: str = "qwen2.5:7b"
    AI_TEMPERATURE: float = 0.7
    AI_MAX_TOKENS: int = 2048
    
    # Настройки API сервера
    API_SERVER_URL: str = "http://api-server:8000"
    API_SERVER_HOST: str = "0.0.0.0"
    API_SERVER_PORT: int = 8000
    
    # Настройки парсинга
    SCRAPE_INTERVAL_SECONDS: int = 3600  # 1 час
    SCRAPE_TIMEOUT_SECONDS: int = 60
    SCRAPE_MAX_RETRIES: int = 3
    SCRAPE_BATCH_SIZE: int = 10
    
    # Настройки Telegram бота
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_ADMIN_CHAT_ID: Optional[int] = None
    TELEGRAM_WEBHOOK_URL: Optional[str] = None
    TELEGRAM_WEBHOOK_PATH: str = "/webhook"
    TELEGRAM_USE_WEBHOOK: bool = False
    
    # Настройки уведомлений
    NOTIFICATIONS_CHECK_INTERVAL: int = 300  # 5 минут
    NOTIFICATIONS_MAX_PER_USER_PER_DAY: int = 50
    NOTIFICATIONS_DAILY_SUMMARY_HOUR: int = 9  # 9 AM
    NOTIFICATIONS_WEEKLY_SUMMARY_DAY: int = 1  # Понедельник
    
    # Настройки мониторинга
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_PORT: int = 9090
    GRAFANA_PORT: int = 3000
    
    # Настройки n8n
    N8N_WEBHOOK_URL: Optional[str] = None
    N8N_USER: str = "admin"
    N8N_PASSWORD: str = "admin123"
    
    # Настройки безопасности
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    JWT_SECRET_KEY: str = "your-jwt-secret-key-here"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # Настройки логирования
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Настройки для внешних API (опционально)
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Настройки прокси (для парсинга)
    USE_PROXY: bool = False
    PROXY_LIST: list[str] = []
    
    # Настройки локализации
    DEFAULT_LANGUAGE: str = "es"
    SUPPORTED_LANGUAGES: list[str] = ["es", "en", "pt", "ru"]
    
    # Настройки валют
    DEFAULT_CURRENCY: str = "ARS"
    USD_TO_ARS_RATE: float = 1000.0  # Обновлять регулярно
    
    # Лимиты и ограничения
    MAX_PROPERTIES_PER_SEARCH: int = 100
    MAX_SAVED_SEARCHES_PER_USER: int = 10
    MAX_FAVORITES_PER_USER: int = 100
    
    # Настройки кеширования
    CACHE_ENABLED: bool = True
    CACHE_DEFAULT_TIMEOUT: int = 300  # 5 минут
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Создаём глобальный экземпляр настроек
settings = Settings()

# Функции для получения настроек
def get_database_url() -> str:
    """Получить URL базы данных"""
    return settings.DATABASE_URL

def get_redis_url() -> str:
    """Получить URL Redis"""
    return settings.REDIS_URL

def is_production() -> bool:
    """Проверить, работаем ли в production"""
    return settings.ENVIRONMENT == "production"

def get_telegram_webhook_url() -> str:
    """Получить полный URL для webhook Telegram"""
    if settings.TELEGRAM_WEBHOOK_URL:
        return f"{settings.TELEGRAM_WEBHOOK_URL}{settings.TELEGRAM_WEBHOOK_PATH}"
    return ""
