from datetime import date, timedelta

def apply_sunday_observed_rule(holiday_date: date, is_holiday_fn) -> date:
    """
    Kenya rule: If a public holiday falls on Sunday, it moves to the next day
    that is NOT already a public holiday (often Monday; could be Tuesday, etc.).
    """
    # Python: Monday=0 ... Sunday=6
    if holiday_date.weekday() != 6:
        return holiday_date

    d = holiday_date + timedelta(days=1)
    while is_holiday_fn(d):
        d += timedelta(days=1)
    return d
