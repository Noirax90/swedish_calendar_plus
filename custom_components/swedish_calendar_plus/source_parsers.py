"""Pure parsing, validation, and history logic for external datasets."""

from __future__ import annotations

import re
from datetime import datetime
from html import unescape
from typing import Final, NotRequired, TypedDict, cast


class NameDaySourceRecord(TypedDict):
    """Relevant fields from one Svenska Akademien API record."""

    date: str
    namnlangd: str
    title: str


class NameDayRecord(TypedDict):
    """Normalized name-day record."""

    day: int
    month: int
    names: list[str]


class NameDayPayload(TypedDict):
    """Normalized name-day dataset."""

    attribution: str
    retrieved_at: str
    source: str
    days: list[NameDayRecord]


class ThemeDayRecord(TypedDict):
    """Normalized or effective-dated theme-day record."""

    day: int
    month: int
    title: str
    url: str
    year: NotRequired[int]
    recurring: NotRequired[bool]
    valid_from: NotRequired[str | None]
    valid_to: NotRequired[str | None]


class ThemeDayPayload(TypedDict):
    """Normalized theme-day dataset."""

    attribution: str
    calendar_years: list[int]
    format_version: int
    retrieved_at: str
    source: str
    days: list[ThemeDayRecord]


class SourceDatasetMetadata(TypedDict):
    """Provenance and change metadata for one normalized dataset."""

    source: str
    retrieved_at: str
    record_count: int
    fingerprint: str


class SourceStorageData(TypedDict, total=False):
    """Persisted last-known-good runtime source data."""

    last_successful_update: str
    last_update_error: str
    consecutive_failures: int
    name_days_metadata: SourceDatasetMetadata
    theme_days_metadata: SourceDatasetMetadata
    name_days: NameDayPayload
    theme_days: ThemeDayPayload


NAME_DAY_URL: Final = (
    "https://sa-admin-live.lb.se/items/names?"
    "fields=*&sort=title&limit=30000&meta=*&page=1"
)
THEME_DAY_URL: Final = "https://temadagar.se/kalender/"
THEME_DAY_BASE_URL: Final = "https://temadagar.se"
MINIMUM_NAME_COUNT: Final = 500
MINIMUM_THEME_DAY_COUNT: Final = 800
MONTHS: Final = {
    "januari": 1,
    "februari": 2,
    "mars": 3,
    "april": 4,
    "maj": 5,
    "juni": 6,
    "juli": 7,
    "augusti": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "december": 12,
}
THEME_TITLE_BACKSLASHES: Final = re.compile(r"\\+")
THEME_TITLE_WHITESPACE: Final = re.compile(r"\s+")


def _normalize_theme_title(raw_title: str) -> str:
    """Normalize source escaping without removing meaningful punctuation."""
    title = THEME_TITLE_BACKSLASHES.sub("", unescape(raw_title))
    return THEME_TITLE_WHITESPACE.sub(" ", title).strip()


def normalize_name_days(payload: object, retrieved_at: str) -> NameDayPayload:
    """Normalize and validate Svenska Akademien's current name-day list."""
    records: dict[tuple[int, int], set[str]] = {}
    source_payload = cast("dict[str, object]", payload)
    for raw_item in cast("list[object]", source_payload["data"]):
        item = cast("NameDaySourceRecord", raw_item)
        if item.get("namnlangd") != "1":
            continue
        source_date = datetime.fromisoformat(item["date"])
        records.setdefault((source_date.month, source_date.day), set()).add(
            item["title"].strip()
        )
    days = [
        {"day": day, "month": month, "names": sorted(names)}
        for (month, day), names in sorted(records.items())
    ]
    if sum(len(item["names"]) for item in days) < MINIMUM_NAME_COUNT:
        msg = "Downloaded name-day dataset is incomplete"
        raise ValueError(msg)
    return {
        "attribution": "Svenska Akademien",
        "retrieved_at": retrieved_at,
        "source": NAME_DAY_URL,
        "days": days,
    }


def parse_theme_day_calendar(
    source: str,
) -> tuple[list[int], list[ThemeDayRecord]]:
    """Parse and validate every annual section published by Temadagar.se."""
    normalized_source = unescape(source).replace("\xa0", " ")
    year_heading_pattern = re.compile(
        r"Kalender\s+med\s+temadagar[^0-9]{0,80}(20\d{2})",
        re.IGNORECASE,
    )
    heading_matches = list(year_heading_pattern.finditer(normalized_source))
    sections = [
        (
            match.group(1),
            normalized_source[
                match.end() : (
                    heading_matches[index + 1].start()
                    if index + 1 < len(heading_matches)
                    else len(normalized_source)
                )
            ],
        )
        for index, match in enumerate(heading_matches)
    ]
    block_pattern = re.compile(
        r"<p><a[^>]*><b>(\d{1,2})\s+([a-zåäö]+)</b></a><br\s*/?>(.*?)</p>",
        re.IGNORECASE | re.DOTALL,
    )
    link_pattern = re.compile(r'<a\s+href="([^"]+)">([^<]+)</a>\s*(\*)?', re.IGNORECASE)
    years = sorted({int(year) for year, _ in sections})
    if not years:
        msg = "Could not determine theme-day calendar years"
        raise ValueError(msg)
    days: list[ThemeDayRecord] = []
    for year_text, section in sections:
        year = int(year_text)
        for day_text, month_text, block in block_pattern.findall(section):
            month = MONTHS.get(month_text.lower())
            if month is None:
                continue
            for path, raw_title, marker in link_pattern.findall(block):
                if not path.startswith("/"):
                    continue
                days.append(
                    {
                        "day": int(day_text),
                        "month": month,
                        "recurring": marker == "*",
                        "title": _normalize_theme_title(raw_title),
                        "url": f"{THEME_DAY_BASE_URL}{path}",
                        "year": year,
                    }
                )
    latest_year = max(years)
    if sum(item["year"] == latest_year for item in days) < MINIMUM_THEME_DAY_COUNT:
        msg = "Downloaded theme-day dataset is incomplete"
        raise ValueError(msg)
    return years, days


def normalize_theme_days(source: str, retrieved_at: str) -> ThemeDayPayload:
    """Normalize the latest complete Temadagar.se calendar snapshot."""
    years, records = parse_theme_day_calendar(source)
    latest_year = max(years)
    return {
        "attribution": "Temadagar.se",
        "calendar_years": years,
        "format_version": 2,
        "retrieved_at": retrieved_at,
        "source": THEME_DAY_URL,
        "days": [item for item in records if item["year"] == latest_year],
    }


def merge_theme_history(
    existing: ThemeDayPayload, current: ThemeDayPayload, retrieved_at: str
) -> ThemeDayPayload:
    """Preserve history while effective-dating detected source changes."""
    existing_days = list(existing.get("days", []))
    if any("valid_from" in item for item in existing_days):
        history = [dict(item) for item in existing_days]
    else:
        baseline_year = max(existing.get("calendar_years", ()), default=None)
        existing_retrieved_at = existing.get("retrieved_at")
        history = [
            {
                "day": item["day"],
                "month": item["month"],
                "title": item["title"],
                "url": item["url"],
                "year": item["year"],
                "recurring": item.get("recurring", False),
                "valid_from": (
                    existing_retrieved_at
                    if existing_retrieved_at
                    and existing_retrieved_at.startswith(f"{item['year']}-")
                    else f"{item['year']}-01-01"
                ),
                "valid_to": (
                    None
                    if item.get("year") == baseline_year
                    else f"{item['year'] + 1}-01-01"
                ),
            }
            for item in existing_days
            if item.get("year") is not None
        ]

    for item in history:
        item["title"] = _normalize_theme_title(item["title"])

    active = {item["url"]: item for item in history if item.get("valid_to") is None}
    incoming = {item["url"]: item for item in current["days"]}
    for url, old in active.items():
        new = incoming.get(url)
        old_recurring = old.get("recurring", True)
        changed = new is not None and (
            any(old[field] != new[field] for field in ("day", "month", "title"))
            or old_recurring != new.get("recurring", False)
            or (not new.get("recurring", False) and old.get("year") != new.get("year"))
        )
        if new is None or changed:
            old["valid_to"] = retrieved_at
    for url, new in incoming.items():
        old = active.get(url)
        if old is not None and old.get("valid_to") is None:
            continue
        history.append(
            {
                "day": new["day"],
                "month": new["month"],
                "title": new["title"],
                "url": new["url"],
                "year": new["year"],
                "recurring": new.get("recurring", False),
                "valid_from": retrieved_at,
            }
        )
    for item in history:
        if item.get("valid_to") is None:
            item.pop("valid_to", None)
    return {**current, "format_version": 2, "days": history}
