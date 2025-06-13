from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
import asyncio
import logging
from typing import List, Dict, Any

from .scraper import PropertyScraper
from .models import Property, database, engine
from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Property Scraper API...")
    await database.connect()
    
    # Инициализация таблиц
    async with engine.begin() as conn:
        await conn.run_sync(Property.metadata.create_all)
    
    # Запуск фонового парсинга
    scraper = PropertyScraper()
    asyncio.create_task(scraper.start_continuous_scraping())
    
    yield
    
    # Shutdown
    await database.disconnect()
    logger.info("Property Scraper API stopped")

app = FastAPI(
    title="Property Scraper API",
    description="API для парсинга недвижимости в Буэнос-Айресе",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Property Scraper API v1.0.0", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/scrape/{site_name}")
async def scrape_site(site_name: str, background_tasks: BackgroundTasks):
    scraper = PropertyScraper()
    
    if site_name not in scraper.sites_config:
        raise HTTPException(status_code=404, detail=f"Site {site_name} not configured")
    
    background_tasks.add_task(scraper.scrape_single_site, site_name)
    
    return {"message": f"Scraping {site_name} started", "site": site_name}

@app.get("/properties")
async def get_properties(
    limit: int = 20,
    offset: int = 0,
    site: str = None,
    min_price: float = None,
    max_price: float = None
):
    query = Property.select()
    
    if site:
        query = query.where(Property.site == site)
    
    if min_price:
        query = query.where(Property.price >= min_price)
    
    if max_price:
        query = query.where(Property.price <= max_price)
    
    query = query.limit(limit).offset(offset)
    
    properties = await database.fetch_all(query)
    
    return {
        "properties": [dict(prop) for prop in properties],
        "count": len(properties),
        "limit": limit,
        "offset": offset
    }

@app.get("/metrics")
async def get_metrics():
    total_properties = await database.fetch_val("SELECT COUNT(*) FROM properties")
    
    metrics = [
        f"# HELP properties_total Total number of properties",
        f"# TYPE properties_total counter",
        f"properties_total {total_properties}"
    ]
    
    return "\n".join(metrics)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
