"""Tests for Home Assistant calendar range semantics."""

from datetime import UTC, datetime

from homeassistant.config_entries import ConfigSubentry
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.swedish_calendar_plus.calendar import SwedishFilteredCalendar
from custom_components.swedish_calendar_plus.const import (
    CATEGORY_HOLIDAYS,
    CONF_CATEGORIES,
    CONF_LANGUAGE,
    DOMAIN,
    SUBENTRY_TYPE_CALENDAR,
)


def _calendar() -> SwedishFilteredCalendar:
    entry = MockConfigEntry(domain=DOMAIN, data={})
    subentry = ConfigSubentry(
        data={CONF_LANGUAGE: "en", CONF_CATEGORIES: [CATEGORY_HOLIDAYS]},
        subentry_type=SUBENTRY_TYPE_CALENDAR,
        title="Holidays",
        unique_id=None,
    )
    return SwedishFilteredCalendar(entry, subentry)


async def test_midnight_end_is_exclusive(hass) -> None:  # noqa: ANN001
    """An event starting at the query's midnight end is excluded."""
    events = await _calendar().async_get_events(
        hass,
        datetime(2026, 12, 24, tzinfo=UTC),
        datetime(2026, 12, 25, tzinfo=UTC),
    )

    assert events == []


async def test_partial_final_day_is_included(hass) -> None:  # noqa: ANN001
    """A non-midnight range end includes events on that final date."""
    events = await _calendar().async_get_events(
        hass,
        datetime(2026, 12, 25, tzinfo=UTC),
        datetime(2026, 12, 25, 12, tzinfo=UTC),
    )

    assert [event.summary for event in events] == ["Christmas Day"]
