"""Tests for runtime localization of generated content."""

import json
from pathlib import Path

import pytest

from custom_components.swedish_calendar_plus.flag_days import flag_days_for_year
from custom_components.swedish_calendar_plus.holidays import (
    holiday_eves_for_year,
    named_holidays_for_year,
)
from custom_components.swedish_calendar_plus.localization import translate


def test_runtime_translations_use_requested_language_and_english_fallback() -> None:
    """Adding another language only requires translations, with safe fallback."""
    assert translate("sv", "event_christmas_eve") == "Julafton"
    assert translate("en", "event_christmas_eve") == "Christmas Eve"
    assert translate("de", "event_christmas_eve") == "Christmas Eve"


def test_every_event_key_exists_in_every_translation_file() -> None:
    """Every supported language must translate every generated event key."""
    expected = {
        *(item.key for item in named_holidays_for_year(2026)),
        *(item.key for item in holiday_eves_for_year(2026)),
        *(item.key for item in flag_days_for_year(2024)),
        *(item.key for item in flag_days_for_year(2026)),
        "bridge_day",
        "sunday",
    }
    directory = (
        Path(__file__).parents[1]
        / "custom_components"
        / "swedish_calendar_plus"
        / "translations"
    )
    translation_files = tuple(directory.glob("*.json"))
    if not translation_files:
        pytest.fail("No translation files found")

    for path in translation_files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        events = {
            key.removeprefix("event_"): value
            for key, value in payload["common"].items()
            if key.startswith("event_")
        }
        assert set(events) == expected, f"Event translations differ in {path.name}"
        assert all(events.values()), f"Empty event translation in {path.name}"
        assert payload["config_subentries"]["calendar"]["entry_type"]
        assert payload["config_subentries"]["calendar"]["initiate_flow"]["user"]
