"""Swedish Calendar Plus integration for Home Assistant."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigSubentry
from homeassistant.const import Platform

from .const import (
    CATEGORY_HOLIDAYS,
    CONF_CALENDAR_NAME,
    CONF_CATEGORIES,
    CONF_INCLUDE_SUNDAYS,
    CONF_LANGUAGE,
    CONFIG_VERSION,
    DEFAULT_CALENDAR_NAME,
    DEFAULT_INCLUDE_SUNDAYS,
    DEFAULT_LANGUAGE,
    SUBENTRY_TYPE_CALENDAR,
)
from .source_update import SourceUpdater
from .sources import load_sources

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import SwedishHolidayCalendarConfigEntry

PLATFORMS: list[Platform] = [
    Platform.CALENDAR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.SENSOR,
]


async def async_migrate_entry(
    hass: HomeAssistant,
    entry: SwedishHolidayCalendarConfigEntry,
) -> bool:
    """Migrate the original one-calendar entry to a calendar subentry."""
    if entry.version >= CONFIG_VERSION:
        return True

    calendar_name = str(entry.data.get(CONF_CALENDAR_NAME, DEFAULT_CALENDAR_NAME))
    language = entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
    hass.config_entries.async_add_subentry(
        entry,
        ConfigSubentry(
            data={
                CONF_LANGUAGE: language,
                CONF_CATEGORIES: [CATEGORY_HOLIDAYS],
            },
            subentry_type=SUBENTRY_TYPE_CALENDAR,
            title=calendar_name,
            unique_id=None,
        ),
    )
    hass.config_entries.async_update_entry(
        entry,
        data={
            CONF_LANGUAGE: language,
            CONF_INCLUDE_SUNDAYS: entry.data.get(
                CONF_INCLUDE_SUNDAYS,
                DEFAULT_INCLUDE_SUNDAYS,
            ),
        },
        version=CONFIG_VERSION,
    )
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SwedishHolidayCalendarConfigEntry,
) -> bool:
    """Set up Swedish Calendar Plus from a config entry."""
    await hass.async_add_executor_job(load_sources)
    entry.runtime_data = SourceUpdater(hass, entry.entry_id)
    await entry.runtime_data.async_load()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: SwedishHolidayCalendarConfigEntry,
) -> bool:
    """Unload a Swedish Calendar Plus config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: SwedishHolidayCalendarConfigEntry,
) -> None:
    """Reload after global options or calendar subentries change."""
    await hass.config_entries.async_reload(entry.entry_id)
