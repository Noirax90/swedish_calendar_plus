"""Tests for effective-dated static dataset updates."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from custom_components.swedish_calendar_plus.source_parsers import merge_theme_history
from custom_components.swedish_calendar_plus.sources import _theme_days_from_payload
from scripts import update_static_data
from scripts.update_static_data import _source_content_changed

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def test_source_comparison_ignores_only_retrieval_timestamp() -> None:
    """A daily check date alone does not count as a source-data change."""
    existing = {
        "retrieved_at": "2026-08-08",
        "source": "https://example.test",
        "days": [{"day": 1, "month": 1}],
    }
    checked_later = {**existing, "retrieved_at": "2026-08-09"}
    changed_data = {
        **checked_later,
        "days": [{"day": 2, "month": 1}],
    }

    assert not _source_content_changed(existing, checked_later)
    assert _source_content_changed(existing, changed_data)


def test_timestamp_only_refresh_does_not_rewrite_dataset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The updater preserves the previous file when only checked-at changed."""
    monkeypatch.setattr(update_static_data, "DATA_DIRECTORY", tmp_path)
    existing = {
        "retrieved_at": "2026-08-08",
        "source": "https://example.test",
        "days": [{"day": 1, "month": 1}],
    }
    path = tmp_path / "source.json"
    path.write_text(json.dumps(existing), encoding="utf-8")

    assert not update_static_data._write_json_if_changed(
        "source.json", {**existing, "retrieved_at": "2026-08-09"}
    )
    assert json.loads(path.read_text(encoding="utf-8")) == existing


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
                "recurring": True,
            },
            {
                "day": 5,
                "month": 10,
                "title": "Removed",
                "url": "https://temadagar.se/removed/",
                "year": 2027,
                "recurring": True,
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
                "recurring": True,
            },
            {
                "day": 7,
                "month": 10,
                "title": "Added",
                "url": "https://temadagar.se/added/",
                "year": 2028,
                "recurring": True,
            },
        ],
    }

    history = merge_theme_history(existing, current, "2028-07-19")["days"]
    by_url: dict[str, list[dict[str, object]]] = {}
    for item in history:
        by_url.setdefault(str(item["url"]), []).append(item)

    assert [item.get("valid_to") for item in by_url["https://temadagar.se/moved/"]] == [
        "2028-07-19",
        None,
    ]
    assert "valid_to" not in by_url["https://temadagar.se/moved/"][1]
    assert by_url["https://temadagar.se/removed/"][0]["valid_to"] == "2028-07-19"
    assert by_url["https://temadagar.se/added/"][0]["valid_from"] == "2028-07-19"


def test_theme_day_history_normalizes_spacing_without_creating_change() -> None:
    """Equivalent source spacing does not create a false history boundary."""
    existing = {
        "calendar_years": [2027],
        "days": [
            {
                "day": 21,
                "month": 4,
                "title": (
                    "Världsdagen\N{NO-BREAK SPACE}för\N{NO-BREAK SPACE}"
                    "kreativitet och innovation"
                ),
                "url": "https://temadagar.se/varldsdagen-for-kreativitet-och-innovation/",
                "year": 2027,
                "recurring": True,
                "valid_from": "2027-01-01",
            }
        ],
    }
    current = {
        "calendar_years": [2027],
        "days": [
            {
                "day": 21,
                "month": 4,
                "title": "Världsdagen för kreativitet och innovation",
                "url": "https://temadagar.se/varldsdagen-for-kreativitet-och-innovation/",
                "year": 2027,
                "recurring": True,
            }
        ],
    }

    records = merge_theme_history(existing, current, "2026-08-13")["days"]

    assert records == [
        {
            "day": 21,
            "month": 4,
            "title": "Världsdagen för kreativitet och innovation",
            "url": "https://temadagar.se/varldsdagen-for-kreativitet-och-innovation/",
            "year": 2027,
            "recurring": True,
            "valid_from": "2027-01-01",
        }
    ]


def test_legacy_theme_history_preserves_each_snapshot_year() -> None:
    """Migrating legacy records keeps both partial and future calendar years."""
    existing = {
        "calendar_years": [2026, 2027],
        "retrieved_at": "2026-07-18",
        "days": [
            {
                "day": 20,
                "month": 7,
                "title": "Existing 2026",
                "url": "https://temadagar.se/existing/",
                "year": 2026,
                "recurring": True,
            },
            {
                "day": 20,
                "month": 7,
                "title": "Existing 2027",
                "url": "https://temadagar.se/existing/",
                "year": 2027,
                "recurring": True,
            },
        ],
    }
    current = {
        "calendar_years": [2026, 2027],
        "days": [
            {
                "day": 20,
                "month": 7,
                "title": "Existing 2027",
                "url": "https://temadagar.se/existing/",
                "year": 2027,
                "recurring": True,
            },
            {
                "day": 10,
                "month": 6,
                "title": "Newly discovered",
                "url": "https://temadagar.se/new/",
                "year": 2027,
                "recurring": True,
            },
        ],
    }

    history = merge_theme_history(existing, current, "2026-07-25")

    assert [item.title for item in _theme_days_from_payload(history, 2026)] == [
        "Existing 2026"
    ]
    assert [item.title for item in _theme_days_from_payload(history, 2027)] == [
        "Newly discovered",
        "Existing 2027",
    ]


def test_recurring_theme_day_projects_until_removed() -> None:
    """A recurring record remains valid in every following year."""
    payload = {
        "days": [
            {
                "day": 10,
                "month": 6,
                "title": "Recurring",
                "url": "https://temadagar.se/recurring/",
                "year": 2027,
                "recurring": True,
                "valid_from": "2026-07-25",
            }
        ]
    }

    assert [item.title for item in _theme_days_from_payload(payload, 2030)] == [
        "Recurring"
    ]


def test_non_recurring_theme_day_only_projects_in_its_source_year() -> None:
    """A non-recurring record is not repeated in following years."""
    payload = {
        "days": [
            {
                "day": 10,
                "month": 6,
                "title": "One-off",
                "url": "https://temadagar.se/one-off/",
                "year": 2027,
                "recurring": False,
                "valid_from": "2026-07-25",
            }
        ]
    }

    assert [item.title for item in _theme_days_from_payload(payload, 2027)] == [
        "One-off"
    ]
    assert _theme_days_from_payload(payload, 2028) == ()


def test_recurring_change_creates_a_new_effective_record() -> None:
    """Changing recurrence closes the old record and starts a new one."""
    existing = {
        "calendar_years": [2027],
        "days": [
            {
                "day": 10,
                "month": 6,
                "title": "Changed",
                "url": "https://temadagar.se/changed/",
                "year": 2027,
                "recurring": True,
                "valid_from": "2026-07-25",
            }
        ],
    }
    current = {
        "calendar_years": [2028],
        "days": [
            {
                "day": 10,
                "month": 6,
                "title": "Changed",
                "url": "https://temadagar.se/changed/",
                "year": 2028,
                "recurring": False,
            }
        ],
    }

    records = merge_theme_history(existing, current, "2027-07-25")["days"]

    assert records[0]["valid_to"] == "2027-07-25"
    assert records[1]["recurring"] is False
    assert records[1]["year"] == 2028
    assert "valid_to" not in records[1]
