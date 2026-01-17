from datetime import date
from pydantic import BaseModel

class HolidayOut(BaseModel):
    date: date
    observedDate: date
    name: str
    type: str
    source: str
    sourceUrl: str | None = None
    publishedDate: date | None = None

class HolidaysResponse(BaseModel):
    country: str
    holidays: list[HolidayOut]
