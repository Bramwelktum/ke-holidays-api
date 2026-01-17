import os
from datetime import date, datetime
import httpx
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
    Nager.Date example baseline source. You can swap this later if you prefer.
    """
    url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/KE"
    r = httpx.get(url, timeout=20)
    r.raise_for_status()
    data = r.json()
    out = []
    for item in data:
        out.append({
            "date": date.fromisoformat(item["date"]),
            "name": item["localName"] or item["name"],
            "type": "public",
            "source": "baseline",
            "source_url": url,
            "published_date": None,
        })
    return out

def fetch_specials_from_scrapers(year: int) -> list[dict]:
    """
    TODO: implement your Kenya Law Gazette + Ministry scraping here.
    For now, return empty list so the API still works.
    Each item must include:
      date, name, type='special', source ('gazette'/'ministry'), source_url, published_date
    """
    return []

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
    Base.metadata.create_all(bind=engine)

    baseline = fetch_baseline_from_nager(year)
    specials = fetch_specials_from_scrapers(year)

    all_items = baseline + specials

    # Helper: is a given date already a holiday? (based on the set we're inserting)
    holiday_dates = set(i["date"] for i in all_items)

    def is_holiday_fn(d: date) -> bool:
        return d in holiday_dates

    # Compute observed dates (Sunday rule)
    for i in all_items:
        i["observed_date"] = apply_sunday_observed_rule(i["date"], is_holiday_fn)

    with Session(engine) as db:
        for i in all_items:
            upsert_holiday(db, i)
        db.commit()

    print(f"Done. Upserted {len(all_items)} holidays for {year}.")

if __name__ == "__main__":
    import sys
    y = int(sys.argv[1]) if len(sys.argv) > 1 else datetime.utcnow().year
    main(y)
