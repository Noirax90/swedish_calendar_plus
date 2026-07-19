"""Diagnostics support for Swedish Calendar Plus."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import SwedishHolidayCalendarConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,  # noqa: ARG001
    entry: SwedishHolidayCalendarConfigEntry,
) -> dict[str, object]:
    """Return useful state without including complete source datasets."""
    source_data = entry.runtime_data.data
    return {
        "config_entry": {
            "version": entry.version,
            "data": dict(entry.data),
            "options": dict(entry.options),
        },
        "calendars": [
            {
                "title": subentry.title,
                "data": dict(subentry.data),
            }
            for subentry in entry.subentries.values()
        ],
        "source_update": {
            "last_successful_update": source_data.get("last_successful_update"),
            "last_update_error": source_data.get("last_update_error"),
            "consecutive_failures": source_data.get("consecutive_failures", 0),
            "name_days": source_data.get("name_days_metadata"),
            "theme_days": source_data.get("theme_days_metadata"),
        },
    }
