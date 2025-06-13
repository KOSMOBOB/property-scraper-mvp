import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
import httpx
from sqlalchemy import insert

from .models import Property, database
from .config import settings

logger = logging.getLogger(__name__)

class PropertyScraper:
    def __init__(self):
        self.sites_config = self._load_sites_config()
        self.crawl4ai_url = settings.CRAWL4AI_URL
        self.ollama_url = settings.OLLAMA_URL
        
    def _load_sites_config(self) -> Dict:
        try:
            with open("/app/configs/sites_config.json", "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load sites config: {e}")
            return {}
    
    async def scrape_single_site(self, site_name: str) -> List[Dict]:
        if site_name not in self.sites_config:
            raise ValueError(f"Site {site_name} not configured")
        
        config = self.sites_config[site_name]
        logger.info(f"Starting scraping {site_name}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.crawl4ai_url}/crawl",
                    json={
                        "urls": [config["url"]],
                        "crawler_config": config["crawler_config"]
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Crawl4AI error: {response.text}")
                    return []
                
                data = response.json()
                extracted_data = data.get("results", [{}])[0].get("extracted_content", [])
                
                processed_properties = await self._process_with_ai(extracted_data, site_name)
                await self._save_properties(processed_properties, site_name)
                
                logger.info(f"Successfully scraped {len(processed_properties)} properties from {site_name}")
                return processed_properties
                
        except Exception as e:
            logger.error(f"Error scraping {site_name}: {e}")
            return []
    
    async def _process_with_ai(self, raw_data: List[Dict], site_name: str) -> List[Dict]:
        if not raw_data:
            return []
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": settings.AI_MODEL,
                    "prompt": self._generate_ai_prompt(raw_data, site_name),
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"AI processing error: {response.status_code} - {response.text}")
                return self._simple_process(raw_data)
    
    def _generate_ai_prompt(self, raw_data: List[Dict], site_name: str) -> str:
        return f"""
        Analyze the following real estate data from {site_name} and extract structured information.
        
        For each property, extract:
        - external_id
        - url
        - neighborhood
        - price_usd
        - price_ars
        - rooms
        - area (in m2)
        - address
        - floor
        - elevator (true/false)
        - parking (true/false)
        - balcony (true/false)
        - terrace (true/false)
        - furnished (true/false)
        - phone
        - description
        - photos (array of urls)
        - published_at (datetime)
        
        Raw data: {json.dumps(raw_data[:3], ensure_ascii=False)}
        
        Return structured JSON array.
        """
    
    def _simple_process(self, raw_data: List[Dict]) -> List[Dict]:
        processed = []
        for item in raw_data:
            if isinstance(item, dict):
                processed.append({
                    "external_id": item.get("external_id", ""),
                    "url": item.get("url", ""),
                    "neighborhood": item.get("neighborhood", ""),
                    "price_usd": item.get("price_usd", 0),
                    "price_ars": item.get("price_ars", 0),
                    "rooms": item.get("rooms", 0),
                    "area": item.get("area", 0),
                    "address": item.get("address", ""),
                    "floor": item.get("floor", ""),
                    "elevator": item.get("elevator", False),
                    "parking": item.get("parking", False),
                    "balcony": item.get("balcony", False),
                    "terrace": item.get("terrace", False),
                    "furnished": item.get("furnished", False),
                    "phone": item.get("phone", ""),
                    "description": item.get("description", ""),
                    "photos": item.get("photos", []),
                    "published_at": item.get("published_at")
                })
        return processed
    
    async def _save_properties(self, properties: List[Dict], site_name: str):
        for prop in properties:
            await database.execute(
                insert(Property).values(
                    external_id=prop["external_id"],
                    source=site_name,
                    url=prop["url"],
                    neighborhood=prop["neighborhood"],
                    price_usd=prop["price_usd"],
                    price_ars=prop["price_ars"],
                    rooms=prop["rooms"],
                    area=prop["area"],
                    address=prop["address"],
                    floor=prop["floor"], 
                    elevator=prop["elevator"],
                    parking=prop["parking"],
                    balcony=prop["balcony"], 
                    terrace=prop["terrace"],
                    furnished=prop["furnished"],
                    phone=prop["phone"],
                    description=prop["description"],
                    photos=prop["photos"],
                    published_at=prop["published_at"],
                    scraped_at=datetime.utcnow(),
                    status="active",
                    first_seen_at=datetime.utcnow(),
                    last_updated_at=datetime.utcnow()
                )
            )
    
    async def start_continuous_scraping(self):
        while True:
            logger.info("Starting scraping cycle...")
            
            for site_name in self.sites_config.keys():
                try:
                    await self.scrape_single_site(site_name)
                    await asyncio.sleep(5)  # Small pause between sites
                except Exception as e:
                    logger.error(f"Error in continuous scraping {site_name}: {e}")
            
            logger.info("Scraping cycle completed. Waiting 1 hour...")
            await asyncio.sleep(3600)  # 1 hour between cycles
