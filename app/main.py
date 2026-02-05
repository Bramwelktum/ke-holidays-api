from contextlib import asynccontextmanager
from datetime import date, datetime
from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func
from .db import Base, engine, get_db, SessionLocal
from .models import Holiday
from .schemas import HolidaysResponse, HolidayOut
from .ingest_utils import perform_ingestion


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    Base.metadata.create_all(bind=engine)
    
    # Auto-seed if empty
    with SessionLocal() as db:
        count = db.query(func.count(Holiday.id)).scalar()
        if count == 0:
            print("📭 Database is empty. Seeding baseline holidays for current year...")
            try:
                # Fast seed (baseline only) for startup
                perform_ingestion(db, datetime.now().year, include_news=False)
                print("✅ Auto-seed complete.")
            except Exception as e:
                print(f"⚠️ Auto-seed failed: {e}")
    yield


app = FastAPI(
    title="Kenya Public Holidays API",
    version="0.1.0",
    description="Free public API for Kenya public holidays with observed-date rule support",
    lifespan=lifespan
)

# Add CORS middleware to allow public access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/v1/holidays", response_model=HolidaysResponse)
def get_holidays(
    year: int | None = Query(default=None, ge=1900, le=2100),
    from_: date | None = Query(default=None, alias="from"),
    to: date | None = Query(default=None, alias="to"),
    db: Session = Depends(get_db),
):
    if year is None and (from_ is None or to is None):
        raise HTTPException(status_code=400, detail="Provide either ?year=YYYY OR ?from=YYYY-MM-DD&to=YYYY-MM-DD")

    stmt = select(Holiday).where(Holiday.country_code == "KE", Holiday.is_active == True)

    # Filtering logic
    start_filter = from_
    end_filter = to

    if year is not None:
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        # Intersection of year and from/to
        start_filter = max(start_filter, year_start) if start_filter else year_start
        end_filter = min(end_filter, year_end) if end_filter else year_end

    if start_filter:
        stmt = stmt.where(Holiday.observed_date >= start_filter)
    if end_filter:
        stmt = stmt.where(Holiday.observed_date <= end_filter)

    rows = db.execute(stmt.order_by(Holiday.observed_date.asc(), Holiday.name.asc())).scalars().all()

    return HolidaysResponse(
        country="KE",
        holidays=[
            HolidayOut(
                date=r.date,
                observedDate=r.observed_date,
                name=r.name,
                type=r.type,
                source=r.source,
                sourceUrl=r.source_url,
                publishedDate=r.published_date,
            )
            for r in rows
        ],
    )

@app.get("/v1/is-holiday")
def is_holiday(
    date_: date = Query(..., alias="date"),
    db: Session = Depends(get_db),
):
    stmt = select(Holiday).where(
        Holiday.country_code == "KE",
        Holiday.is_active == True,
        Holiday.observed_date == date_,
    )
    r = db.execute(stmt).scalars().first()
    return {"date": date_, "isHoliday": r is not None, "holiday": (None if r is None else {
        "name": r.name,
        "type": r.type,
        "source": r.source,
        "date": r.date,
        "observedDate": r.observed_date,
    })}
