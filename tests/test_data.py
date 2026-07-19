"""Tests for effective shared and per-calendar settings."""

from datetime import date
from types import SimpleNamespace

from homeassistant.config_entries import ConfigSubentry
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.swedish_calendar_plus.calendar import _items_between
from custom_components.swedish_calendar_plus.const import (
    CATEGORY_FLAG_DAYS,
    CATEGORY_NAME_DAYS,
    CONF_CATEGORIES,
    CONF_INCLUDE_BRIDGE_DAYS,
    CONF_LANGUAGE,
    CONF_OVERRIDE_SHARED_EVE_SETTINGS,
    DOMAIN,
    SUBENTRY_TYPE_CALENDAR,
)
from custom_components.swedish_calendar_plus.data import calendar_included_eves
from custom_components.swedish_calendar_plus.sources import NameDay


def _subentry(data: dict[str, object]) -> ConfigSubentry:
    return ConfigSubentry(
        data=data,
        subentry_type=SUBENTRY_TYPE_CALENDAR,
        title="Calendar",
        unique_id=None,
    )


def test_calendar_can_inherit_or_override_shared_red_day_eves() -> None:
    """A calendar inherits shared eve settings unless override is enabled."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "red_day_christmas_eve": True,
            "red_day_new_years_eve": False,
        },
    )

    assert calendar_included_eves(entry, _subentry({})) == frozenset({"christmas_eve"})
    assert calendar_included_eves(
        entry,
        _subentry(
            {
                CONF_OVERRIDE_SHARED_EVE_SETTINGS: True,
                "include_christmas_eve": False,
                "include_new_years_eve": True,
            }
        ),
    ) == frozenset({"new_years_eve"})


def test_calendar_include_setting_does_not_change_shared_red_day_policy() -> None:
    """Calendar-specific include switches only add events to that calendar."""
    entry = MockConfigEntry(domain=DOMAIN, data={"red_day_christmas_eve": False})
    calendar = _subentry(
        {
            CONF_LANGUAGE: "en",
            CONF_CATEGORIES: [],
            CONF_OVERRIDE_SHARED_EVE_SETTINGS: True,
            "include_christmas_eve": True,
        }
    )

    items = _items_between(
        entry,
        calendar,
        date(2026, 12, 24),
        date(2026, 12, 25),
    )

    assert [(item.date, item.summary) for item in items] == [
        (date(2026, 12, 24), "Christmas Eve")
    ]


def test_calendar_can_include_bridge_days_as_named_events() -> None:
    """The calendar switch adds a localized event without shared settings."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    calendar = _subentry(
        {
            CONF_LANGUAGE: "en",
            CONF_CATEGORIES: [],
            CONF_INCLUDE_BRIDGE_DAYS: True,
        }
    )

    items = _items_between(
        entry,
        calendar,
        date(2026, 5, 15),
        date(2026, 5, 16),
    )

    assert [(item.date, item.summary) for item in items] == [
        (date(2026, 5, 15), "Bridge day")
    ]

    swedish_items = _items_between(
        entry,
        _subentry(
            {
                CONF_LANGUAGE: "sv",
                CONF_CATEGORIES: [],
                CONF_INCLUDE_BRIDGE_DAYS: True,
            }
        ),
        date(2026, 5, 15),
        date(2026, 5, 16),
    )
    assert [item.summary for item in swedish_items] == ["Klämdag"]


def test_name_day_event_contains_only_comma_separated_names() -> None:
    """Name-day summaries contain no label, colon, or trailing separator."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.runtime_data = SimpleNamespace(
        sources=SimpleNamespace(
            name_days_for_year=lambda _year: (
                NameDay(date(2026, 7, 19), ("Sara", "Margareta")),
            )
        )
    )
    calendar = _subentry(
        {
            CONF_LANGUAGE: "sv",
            CONF_CATEGORIES: [CATEGORY_NAME_DAYS],
        }
    )

    items = _items_between(
        entry,
        calendar,
        date(2026, 7, 19),
        date(2026, 7, 20),
    )

    assert [item.summary for item in items] == ["Sara, Margareta"]


def test_flag_days_are_an_independent_calendar_category() -> None:
    """Flag days can be selected without enabling holidays or red-day rules."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    calendar = _subentry(
        {
            CONF_LANGUAGE: "en",
            CONF_CATEGORIES: [CATEGORY_FLAG_DAYS],
        }
    )

    items = _items_between(
        entry,
        calendar,
        date(2026, 1, 28),
        date(2026, 1, 29),
    )

    assert [(item.date, item.summary) for item in items] == [
        (date(2026, 1, 28), "King Carl XVI Gustaf's name day")
    ]
