"""Tests for effective-dated static dataset updates."""

from custom_components.swedish_calendar_plus.source_parsers import (
    merge_theme_history,
)


def test_theme_day_history_dates_changes_additions_and_removals() -> None:
    """A refresh preserves old facts and dates every detected change."""
    existing = {
        "calendar_years": [2027],
        "days": [
            {
                "day": 4,
                "month": 10,
                "title": "Moved",
                "url": "https://temadagar.se/moved/",
                "year": 2027,
            },
            {
                "day": 5,
                "month": 10,
                "title": "Removed",
                "url": "https://temadagar.se/removed/",
                "year": 2027,
            },
        ],
    }
    current = {
        "calendar_years": [2028],
        "days": [
            {
                "day": 6,
                "month": 10,
                "title": "Moved",
                "url": "https://temadagar.se/moved/",
                "year": 2028,
            },
            {
                "day": 7,
                "month": 10,
                "title": "Added",
                "url": "https://temadagar.se/added/",
                "year": 2028,
            },
        ],
    }

    history = merge_theme_history(existing, current, "2028-07-19")["days"]
    by_url: dict[str, list[dict[str, object]]] = {}
    for item in history:
        by_url.setdefault(str(item["url"]), []).append(item)

    assert [item["valid_to"] for item in by_url["https://temadagar.se/moved/"]] == [
        "2028-07-19",
        None,
    ]
    assert by_url["https://temadagar.se/removed/"][0]["valid_to"] == "2028-07-19"
    assert by_url["https://temadagar.se/added/"][0]["valid_from"] == "2028-07-19"
