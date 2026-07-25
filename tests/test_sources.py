"""Tests for bundled external calendar sources."""

from datetime import date

from custom_components.swedish_calendar_plus.sources import (
    NameDay,
    SourceRepository,
    _theme_days_from_payload,
    name_days_for_year,
    theme_days_for_year,
)


def test_name_day_snapshot_and_leap_day() -> None:
    """The bundled snapshot is complete and leap day is only projected when valid."""
    leap_year = name_days_for_year(2028)
    common_year = name_days_for_year(2027)

    assert sum(len(item.names) for item in leap_year) == 630
    assert sum(len(item.names) for item in common_year) < 630
    assert any(item.date.month == 2 and item.date.day == 29 for item in leap_year)
    assert not any(item.date.month == 2 and item.date.day == 29 for item in common_year)


def test_theme_days_include_attributed_links() -> None:
    """Theme-day records retain canonical Temadagar links."""
    items = theme_days_for_year(2027)

    assert len(items) >= 800
    assert all(item.url.startswith("https://temadagar.se/") for item in items)
    assert any(item.title == "Kanelbullens dag" for item in items)


def test_only_recurring_theme_days_are_projected_forward() -> None:
    """Only latest records marked recurring remain available in future years."""
    current = theme_days_for_year(2027)
    future = theme_days_for_year(2030)

    assert len(future) < len(current)
    assert any(item.title == "Kanelbullens dag" for item in future)


def test_theme_day_changes_can_be_effective_dated() -> None:
    """Moved theme days retain history and change only from their valid date."""
    payload = {
        "days": [
            {
                "day": 4,
                "month": 10,
                "title": "Exempeldagen",
                "url": "https://temadagar.se/exempeldagen/",
                "valid_from": "2027-01-01",
                "valid_to": "2028-07-01",
            },
            {
                "day": 5,
                "month": 10,
                "title": "Exempeldagen",
                "url": "https://temadagar.se/exempeldagen/",
                "valid_from": "2028-07-01",
            },
        ]
    }

    assert _theme_days_from_payload(payload, 2027)[0].date == date(2027, 10, 4)
    assert _theme_days_from_payload(payload, 2028)[0].date == date(2028, 10, 5)


def test_runtime_sources_are_scoped_to_their_repository() -> None:
    """Activating runtime data cannot leak into another config-entry repository."""
    updated = SourceRepository()
    untouched = SourceRepository()
    updated.activate(
        {
            "attribution": "Svenska Akademien",
            "retrieved_at": "2026-07-19",
            "source": "https://example.test/names",
            "days": [{"day": 19, "month": 7, "names": ["Runtime"]}],
        },
        None,
    )

    assert updated.name_days_for_year(2026) == (
        NameDay(date(2026, 7, 19), ("Runtime",)),
    )
    assert untouched.name_days_for_year(2026) != updated.name_days_for_year(2026)
