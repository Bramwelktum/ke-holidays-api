import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.db import Base
from app.ingest_utils import perform_ingestion

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5433/holidays")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def main(year: int):
    print(f"🚀 Starting holiday ingestion for {year}...")
    try:
        print(f"🔗 Connecting to database...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables verified/created.")
    except Exception as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)

    print(f"📡 Fetching and scraping holidays for {year}...")
    with Session(engine) as db:
        count = perform_ingestion(db, year, include_news=True)
        print(f"🏁 Successfully ingested {count} holidays for {year}!")

if __name__ == "__main__":
    y = int(sys.argv[1]) if len(sys.argv) > 1 else datetime.now().year
    main(y)


