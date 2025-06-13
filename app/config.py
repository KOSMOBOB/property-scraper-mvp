from pydantic import BaseSettings

class Settings(BaseSettings):
    # Общие настройки
    APP_NAME: str = "Property Scraper"
    APP_VERSION: str = "1.0.0"
    
    # Настройки базы данных
    DATABASE_URL: str = "postgresql://scraper:scraper123@postgres:5432/property_scraper"
    
    # Настройки Redis
    REDIS_URL: str = "redis://redis:6379"
    
    # Настройки Crawl4AI
    CRAWL4AI_URL: str = "http://crawl4ai:11235"
    
    # Настройки Ollama
    OLLAMA_URL: str = "http://ollama:11434"
    AI_MODEL: str = "qwen2.5:7b"
    
    # Настройки парсинга
    SCRAPE_INTERVAL_SECONDS: int = 3600  # 1 час
    SCRAPE_TIMEOUT_SECONDS: int = 60
    
    # Настройки Telegram бота
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_ADMIN_CHAT_ID: int
    
    # Настройки мониторинга
    SENTRY_DSN: str = None
    PROMETHEUS_PORT: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
