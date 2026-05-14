from __future__ import annotations

import re
from datetime import datetime, timedelta


def parse_relative_date(text: str, now: datetime | None = None) -> str | None:
    now = now or datetime.now()
    mapping = {
        "hôm nay": now,
        "chiều nay": now,
        "toi nay": now,
        "tối nay": now,
        "hôm qua": now - timedelta(days=1),
        "hôm kia": now - timedelta(days=2),
        "mai": now + timedelta(days=1),
        "ngày mai": now + timedelta(days=1),
        "mốt": now + timedelta(days=2),
        "ngày mốt": now + timedelta(days=2),
        "tuần sau": now + timedelta(days=7),
    }
    lowered = text.lower()
    for phrase, dt in mapping.items():
        if phrase in lowered:
            return dt.strftime("%Y-%m-%d")

    weekday_match = re.search(r"thứ\s*(\d)", lowered)
    if weekday_match:
        target = int(weekday_match.group(1))
        today = now.isoweekday()
        offset = (target - today) % 7
        offset = 7 if offset == 0 else offset
        return (now + timedelta(days=offset)).strftime("%Y-%m-%d")
    return None

