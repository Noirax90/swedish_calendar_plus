"""Tests for deterministic external-source parsing."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from custom_components.swedish_calendar_plus import source_parsers

if TYPE_CHECKING:
    import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def test_theme_title_normalization_removes_source_backslashes() -> None:
    """One or several source backslashes do not leak into event titles."""
    for raw_title in (r"Saint Patrick\'s day", r"Saint Patrick\\'s day"):
        assert source_parsers._normalize_theme_title(raw_title) == "Saint Patrick's day"


def test_temadagar_html_fixture_is_parsed_without_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Representative Temadagar markup retains dates, links, and recurrence."""
    monkeypatch.setattr(source_parsers, "MINIMUM_THEME_DAY_COUNT", 5)
    source = (FIXTURES / "temadagar_calendar.html").read_text(encoding="utf-8")

    years, days = source_parsers.parse_theme_day_calendar(source)

    assert years == [2027]
    assert days == [
        {
            "day": 17,
            "month": 3,
            "recurring": True,
            "title": "Saint Patrick's day",
            "url": "https://temadagar.se/saint-patricks-day/",
            "year": 2027,
        },
        {
            "day": 17,
            "month": 3,
            "recurring": False,
            "title": "PANDAS/PANS Awareness Day",
            "url": "https://temadagar.se/pandas-pans-awareness-day/",
            "year": 2027,
        },
        {
            "day": 4,
            "month": 10,
            "recurring": False,
            "title": "Kanelbullens dag",
            "url": "https://temadagar.se/kanelbullens-dag/",
            "year": 2027,
        },
        {
            "day": 4,
            "month": 10,
            "recurring": True,
            "title": "Djurens dag",
            "url": "https://temadagar.se/djurens-dag/",
            "year": 2027,
        },
        {
            "day": 10,
            "month": 12,
            "recurring": False,
            "title": "Mänskliga rättigheternas dag",
            "url": "https://temadagar.se/manskliga-rattigheternas-dag/",
            "year": 2027,
        },
    ]
