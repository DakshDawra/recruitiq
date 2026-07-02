import datetime

def parse_date(date_str):
    """
    Safely parses a YYYY-MM-DD date string.
    Returns a datetime object or None if invalid.
    """
    if not date_str:
        return None
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None
