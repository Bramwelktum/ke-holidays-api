import os
import sys
import re
from datetime import date, datetime
import httpx
from bs4 import BeautifulSoup
from dateutil import parser
from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models import Holiday
from app.db import Base
from app.logic import apply_sunday_observed_rule

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5433/holidays")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def fetch_baseline_from_nager(year: int) -> list[dict]:
    """
    Nager.Date example baseline source.
    """
    print(f"📡 Fetching baseline holidays for {year} from Nager.Date...")
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
                "published_date": None,
            })
        print(f"✅ Found {len(out)} baseline holidays.")
        return out
    except Exception as e:
        print(f"⚠️ Could not fetch baseline holidays: {e}")
        return []

def scrape_news_source(url: str, name: str, selectors: dict) -> list[dict]:
    """
    Generic scraper for news sites search results.
    """
    print(f"🔍 Searching {name} for surprise holidays...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    try:
        r = httpx.get(url, headers=headers, timeout=25)
        if r.status_code != 200:
            print(f"   ❌ {name} returned status {r.status_code}")
            return []
        
        soup = BeautifulSoup(r.text, 'html.parser')
        articles = soup.select(selectors['container'])
        found = []
        
        # Keywords to look for
        keywords = ["declare", "public holiday", "gazette", "holiday"]
        
        for art in articles:
            title_node = art.select_one(selectors['title'])
            if not title_node: continue
            title = title_node.get_text().strip()
            link = title_node.get('href', url)
            if not link.startswith('http'):
                link = os.path.join(url, link.lstrip('/'))
            
            # Check if title suggests a holiday announcement
            title_lower = title.lower()
            if any(kw in title_lower for kw in keywords):
                # Try to extract a date from the title
                # Look for things like "October 10", "1st November", etc.
                try:
                    # Clean title for parser (remove common news prefixes)
                    clean_title = re.sub(r'^(Live|News|Video|Photos):', '', title, flags=re.I).strip()
                    # extract date parts
                    date_match = re.search(r'(\d+(st|nd|rd|th)?\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*|\d{4})', clean_title, re.I)
                    
                    if date_match:
                        # Use parser but hint at the current year or specific year
                        # We only want to pick up dates that look like specific days
                        parsed_date = parser.parse(clean_title, fuzzy=True, default=datetime(datetime.now().year, 1, 1))
                        
                        # Only accept if it's within a reasonable range of the target year
                        # and not just a year number
                        found.append({
                            "date": parsed_date.date(),
                            "name": title,
                            "type": "special",
                            "source": name.lower(),
                            "source_url": link,
                            "published_date": None,
                        })
                except:
                    continue
        
        print(f"   ✅ Found {len(found)} potential matches on {name}.")
        return found
    except Exception as e:
        print(f"   ⚠️ Error scraping {name}: {e}")
        return []

def fetch_specials_from_scrapers(year: int) -> list[dict]:
    """
    Scrape Kenya news sources for surprise holidays.
    """
    sources = [
        {
            "name": "NTV Kenya",
            "url": "https://ntvkenya.co.ke/?s=public+holiday+declared",
            "selectors": {"container": "article", "title": "h3.entry-title a"}
        },
        {
            "name": "KTN News",
            "url": "https://www.standardmedia.co.ke/search?q=public+holiday+declared",
            "selectors": {"container": ".col-md-8", "title": "h4 a"}
        }
    ]
    
    all_specials = []
    for src in sources:
        results = scrape_news_source(src['url'], src['name'], src['selectors'])
        all_specials.extend(results)
    
    # Filter by year and deduplicate
    current_year_specials = [s for s in all_specials if s['date'].year == year]
    
    # Simple deduplication by date
    unique = {}
    for s in current_year_specials:
        if s['date'] not in unique:
            unique[s['date']] = s
            
    print(f"✨ Total unique surprise holidays found for {year}: {len(unique)}")
    return list(unique.values())

def upsert_holiday(db: Session, h: dict):
    existing = db.execute(
        select(Holiday).where(
            Holiday.country_code == "KE",
            Holiday.date == h["date"],
            Holiday.name == h["name"],
            Holiday.type == h["type"],
        )
    ).scalars().first()

    if existing:
        existing.observed_date = h["observed_date"]
        existing.source = h["source"]
        existing.source_url = h.get("source_url")
        existing.published_date = h.get("published_date")
        existing.is_active = True
    else:
        db.add(Holiday(
            country_code="KE",
            date=h["date"],
            observed_date=h["observed_date"],
            name=h["name"],
            type=h["type"],
            source=h["source"],
            source_url=h.get("source_url"),
            published_date=h.get("published_date"),
            is_active=True,
        ))

def main(year: int):
    print(f"🚀 Starting holiday ingestion for {year}...")
    
    try:
        print(f"🔗 Connecting to database...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables verified/created.")
    except Exception as e:
        print(f"❌ Database error: {e}")
        print("Please ensure DATABASE_URL is correct and the database is accessible.")
        sys.exit(1)

    baseline = fetch_baseline_from_nager(year)
    specials = fetch_specials_from_scrapers(year)

    all_items = baseline + specials

    if not all_items:
        print("⚠️ No holidays found to ingest.")
        return

    # Helper: is a given date already a holiday? 
    holiday_dates = set(i["date"] for i in all_items)

    def is_holiday_fn(d: date) -> bool:
        return d in holiday_dates

    # Compute observed dates (Sunday rule)
    print("📏 Applying Sunday-observed-rule...")
    for i in all_items:
        i["observed_date"] = apply_sunday_observed_rule(i["date"], is_holiday_fn)

    print(f"💾 Saving {len(all_items)} holidays to database...")
    with Session(engine) as db:
        for i in all_items:
            upsert_holiday(db, i)
        try:
            db.commit()
            print(f"🏁 Successfully ingested {len(all_items)} holidays for {year}!")
        except Exception as e:
            db.rollback()
            print(f"❌ Failed to commit to database: {e}")

if __name__ == "__main__":
    y = int(sys.argv[1]) if len(sys.argv) > 1 else datetime.now().year
    main(y)

