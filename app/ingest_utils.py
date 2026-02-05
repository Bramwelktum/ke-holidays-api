import os
import re
from datetime import date, datetime
import httpx
from bs4 import BeautifulSoup
from dateutil import parser
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Holiday
from .logic import apply_sunday_observed_rule

def fetch_baseline_from_nager(year: int) -> list[dict]:
    """Fetch base holidays for a country year."""
    url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/KE"
    try:
        r = httpx.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()
        out = []
        for item in data:
            out.append({
                "date": date.fromisoformat(item["date"]),
                "name": item["localName"] or item["name"],
                "type": "public",
                "source": "nager.date",
                "source_url": url,
            })
        return out
    except Exception as e:
        print(f"Warning: Could not fetch baseline: {e}")
        return []

def scrape_news_source(url: str, name: str, selectors: dict, target_year: int) -> list[dict]:
    """Generic news scraper."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    try:
        r = httpx.get(url, headers=headers, timeout=25)
        if r.status_code != 200: return []
        
        soup = BeautifulSoup(r.text, 'html.parser')
        articles = soup.select(selectors['container'])
        found = []
        keywords = ["declare", "public holiday", "gazette", "holiday"]
        
        for art in articles:
            title_node = art.select_one(selectors['title'])
            if not title_node: continue
            title = title_node.get_text().strip()
            link = title_node.get('href', url)
            if not link.startswith('http'):
                link = os.path.join(url, link.lstrip('/'))
            
            title_lower = title.lower()
            if any(kw in title_lower for kw in keywords):
                try:
                    clean_title = re.sub(r'^(Live|News|Video|Photos):', '', title, flags=re.I).strip()
                    date_match = re.search(r'(\d+(st|nd|rd|th)?\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*|\d{4})', clean_title, re.I)
                    if date_match:
                        # Use target_year as default so "Oct 10" becomes "2025-10-10" if ingesting 2025
                        parsed_date = parser.parse(clean_title, fuzzy=True, default=datetime(target_year, 1, 1))
                        
                        # Only accept if the parsed date actually falls in our target year
                        if parsed_date.year == target_year:
                            found.append({
                                "date": parsed_date.date(),
                                "name": title,
                                "type": "special",
                                "source": name.lower(),
                                "source_url": link,
                            })
                except: continue
        return found
    except Exception: return []

def perform_ingestion(db: Session, year: int, include_news: bool = True):
    """Core logic to ingest holidays."""
    baseline = fetch_baseline_from_nager(year)
    specials = []
    
    if include_news:
        sources = [
            {"name": "NTV Kenya", "url": "https://ntvkenya.co.ke/?s=public+holiday+declared", "selectors": {"container": "article", "title": "h3.entry-title a"}},
            {"name": "KTN News", "url": "https://www.standardmedia.co.ke/search?q=public+holiday+declared", "selectors": {"container": ".col-md-8", "title": "h4 a"}},
        ]
        for src in sources:
            specials.extend(scrape_news_source(src['url'], src['name'], src['selectors'], year))

    all_items = baseline + specials
    holiday_dates = set(i["date"] for i in all_items)

    def is_holiday_fn(d: date) -> bool:
        return d in holiday_dates

    for i in all_items:
        i["observed_date"] = apply_sunday_observed_rule(i["date"], is_holiday_fn)

        # Upsert
        existing = db.execute(
            select(Holiday).where(
                Holiday.country_code == "KE",
                Holiday.date == i["date"],
                Holiday.name == i["name"],
                Holiday.type == i["type"],
            )
        ).scalars().first()

        if existing:
            existing.observed_date = i["observed_date"]
            existing.source = i["source"]
            existing.source_url = i.get("source_url")
        else:
            db.add(Holiday(
                country_code="KE",
                date=i["date"],
                observed_date=i["observed_date"],
                name=i["name"],
                type=i["type"],
                source=i["source"],
                source_url=i.get("source_url"),
            ))
    db.commit()
    return len(all_items)
