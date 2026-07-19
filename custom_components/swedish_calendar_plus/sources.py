"""Load bundled name-day and theme-day calendar sources."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from functools import cache
from importlib.resources import files
from typing import TYPE_CHECKING, Literal, cast, overload

from .localization import load_translations

if TYPE_CHECKING:
    from .source_parsers import NameDayPayload, ThemeDayPayload

NAME_DAY_SOURCE = "Svenska Akademien"
THEME_DAY_SOURCE = "Temadagar.se"


@dataclass(frozen=True, slots=True)
class NameDay:
    """Names celebrated on a calendar date."""

    date: date
    names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ThemeDay:
    """A theme day from Temadagar.se."""

    date: date
    title: str
    url: str


@overload
def _load(filename: Literal["name_days.json"]) -> NameDayPayload: ...


@overload
def _load(filename: Literal["theme_days.json"]) -> ThemeDayPayload: ...


@cache
def _load(filename: str) -> NameDayPayload | ThemeDayPayload:
    path = files(__package__).joinpath("data", filename)
    return cast(
        "NameDayPayload | ThemeDayPayload",
        json.loads(path.read_text(encoding="utf-8")),
    )


def load_theme_day_payload() -> ThemeDayPayload:
    """Return the bundled normalized theme-day dataset."""
    return _load("theme_days.json")


def load_sources() -> None:
    """Load bundled datasets into memory from an executor thread."""
    _load("name_days.json")
    _load("theme_days.json")
    load_translations()


def _name_days_from_payload(payload: NameDayPayload, year: int) -> tuple[NameDay, ...]:
    """Project a normalized name-day dataset onto a year."""
    result: list[NameDay] = []
    for item in payload["days"]:
        try:
            event_date = date(year, item["month"], item["day"])
        except ValueError:
            continue
        result.append(NameDay(event_date, tuple(item["names"])))
    return tuple(result)


def _theme_days_from_payload(
    payload: ThemeDayPayload, year: int
) -> tuple[ThemeDay, ...]:
    """Project effective-dated theme-day records onto a requested year."""
    calendar_years = tuple(payload.get("calendar_years", ()))
    latest_snapshot_year = max(calendar_years, default=None)
    records: dict[tuple[int, int, str], ThemeDay] = {}
    for item in payload["days"]:
        valid_from = (
            date.fromisoformat(item["valid_from"]) if item.get("valid_from") else None
        )
        valid_to = (
            date.fromisoformat(item["valid_to"]) if item.get("valid_to") else None
        )

        if valid_from is None:
            source_year = item["year"]
            should_project = source_year == year or (
                latest_snapshot_year is not None
                and year > latest_snapshot_year
                and source_year == latest_snapshot_year
            )
            if not should_project:
                continue

        try:
            event_date = date(year, item["month"], item["day"])
        except ValueError:
            continue
        if valid_from is not None and event_date < valid_from:
            continue
        if valid_to is not None and event_date >= valid_to:
            continue
        records[(event_date.month, event_date.day, item["url"])] = ThemeDay(
            event_date,
            item["title"],
            item["url"],
        )
    return tuple(sorted(records.values(), key=lambda item: (item.date, item.title)))


def theme_days_for_year(year: int) -> tuple[ThemeDay, ...]:
    """Return bundled theme days projected onto the requested year."""
    return _theme_days_from_payload(_load("theme_days.json"), year)


def name_days_for_year(year: int) -> tuple[NameDay, ...]:
    """Return bundled name days projected onto the requested year."""
    return _name_days_from_payload(_load("name_days.json"), year)


class SourceRepository:
    """Resolve runtime datasets with deterministic bundled fallbacks."""

    def __init__(self) -> None:
        """Initialize without runtime overrides."""
        self._name_days: NameDayPayload | None = None
        self._theme_days: ThemeDayPayload | None = None

    def activate(
        self,
        name_days: NameDayPayload | None,
        theme_days: ThemeDayPayload | None,
    ) -> None:
        """Activate already validated runtime datasets."""
        self._name_days = name_days
        self._theme_days = theme_days

    def name_days_for_year(self, year: int) -> tuple[NameDay, ...]:
        """Return active name days, falling back to the bundled dataset."""
        return _name_days_from_payload(self._name_days or _load("name_days.json"), year)

    def theme_days_for_year(self, year: int) -> tuple[ThemeDay, ...]:
        """Return active theme days, falling back to the bundled dataset."""
        return _theme_days_from_payload(
            self._theme_days or _load("theme_days.json"), year
        )
