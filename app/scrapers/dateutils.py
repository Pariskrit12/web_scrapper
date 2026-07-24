import re
from datetime import datetime, timedelta, timezone
from typing import Optional

_RELATIVE_RE = re.compile(
    r"(?P<value>\d+)\s+(?P<unit>second|minute|hour|day|week|month|year)s?\s+ago",
    re.IGNORECASE,
)

_UNIT_TO_KWARG = {
    "second": "seconds",
    "minute": "minutes",
    "hour": "hours",
    "day": "days",
    "week": "weeks",
}

_ABSOLUTE_FORMATS = ("%b %d, %Y", "%B %d, %Y")


def parse_fuzzy_date(text: Optional[str], now: Optional[datetime] = None) -> Optional[datetime]:
    """Best-effort parse of relative ("3 days ago") or absolute ("Jun 10, 2026")
    date strings as commonly returned by search widgets / JSON APIs that don't
    expose ISO timestamps. Returns None if the format isn't recognized."""
    if not text:
        return None
    text = text.strip()
    now = now or datetime.now(timezone.utc)
    # Search widgets often prefix a snippet with "<date> ...<description>";
    # only the leading line/segment is a date candidate.
    lead = text.split("\n", 1)[0].strip()

    match = _RELATIVE_RE.search(lead) or _RELATIVE_RE.search(text)
    if match:
        value = int(match.group("value"))
        unit = match.group("unit").lower()
        if unit == "month":
            return now - timedelta(days=30 * value)
        if unit == "year":
            return now - timedelta(days=365 * value)
        kwarg = _UNIT_TO_KWARG.get(unit)
        if kwarg:
            return now - timedelta(**{kwarg: value})

    for fmt in _ABSOLUTE_FORMATS:
        try:
            return datetime.strptime(lead, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
