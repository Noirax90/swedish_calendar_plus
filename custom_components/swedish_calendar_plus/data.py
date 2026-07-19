"""Types and configuration helpers for Swedish Calendar Plus."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from .const import (
    CONF_CATEGORIES,
    CONF_INCLUDE_BRIDGE_DAYS,
    CONF_INCLUDE_SUNDAYS,
    CONF_LANGUAGE,
    CONF_OVERRIDE_SHARED_EVE_SETTINGS,
    CONF_RED_DAY_BRIDGE_DAYS,
    DEFAULT_CATEGORIES,
    DEFAULT_INCLUDE_SUNDAYS,
    DEFAULT_LANGUAGE,
    RED_DAY_EVE_KEYS,
)
from .holidays import DayPolicy

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry, ConfigSubentry

    from .holidays import Language
    from .source_update import SourceUpdater

type SwedishHolidayCalendarConfigEntry = ConfigEntry[SourceUpdater]


def config_value(
    entry: SwedishHolidayCalendarConfigEntry, key: str, default: object
) -> object:
    """Return an option, falling back to initial config-entry data."""
    return entry.options.get(key, entry.data.get(key, default))


def sensor_language(entry: SwedishHolidayCalendarConfigEntry) -> Language:
    """Return the language used by shared sensors."""
    return cast("Language", config_value(entry, CONF_LANGUAGE, DEFAULT_LANGUAGE))


def include_sundays(entry: SwedishHolidayCalendarConfigEntry) -> bool:
    """Return whether every Sunday counts as a red day."""
    return bool(config_value(entry, CONF_INCLUDE_SUNDAYS, DEFAULT_INCLUDE_SUNDAYS))


def shared_red_day_eves(
    entry: SwedishHolidayCalendarConfigEntry,
) -> frozenset[str]:
    """Return holiday eves globally configured to count as red days."""
    return frozenset(
        key
        for key in RED_DAY_EVE_KEYS
        if bool(
            entry.options.get(f"red_day_{key}", entry.data.get(f"red_day_{key}", False))
        )
    )


def shared_red_day_bridge_days(entry: SwedishHolidayCalendarConfigEntry) -> bool:
    """Return whether bridge days globally count as red days."""
    return bool(
        entry.options.get(
            CONF_RED_DAY_BRIDGE_DAYS,
            entry.data.get(CONF_RED_DAY_BRIDGE_DAYS, False),
        )
    )


def day_policy(entry: SwedishHolidayCalendarConfigEntry) -> DayPolicy:
    """Return all shared rules that determine whether a date is red."""
    return DayPolicy(
        include_sundays=include_sundays(entry),
        red_day_eves=shared_red_day_eves(entry),
        include_bridge_days=shared_red_day_bridge_days(entry),
    )


def calendar_included_eves(
    entry: SwedishHolidayCalendarConfigEntry,
    subentry: ConfigSubentry,
) -> frozenset[str]:
    """Return the holiday eves that should be included in a calendar."""
    if not subentry.data.get(CONF_OVERRIDE_SHARED_EVE_SETTINGS, False):
        return shared_red_day_eves(entry)
    return frozenset(
        key for key in RED_DAY_EVE_KEYS if subentry.data.get(f"include_{key}", False)
    )


def calendar_includes_bridge_days(subentry: ConfigSubentry) -> bool:
    """Return whether bridge days should be included in a calendar."""
    return bool(subentry.data.get(CONF_INCLUDE_BRIDGE_DAYS, False))


def calendar_language(subentry: ConfigSubentry) -> Language:
    """Return a calendar subentry's event language."""
    return cast("Language", subentry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE))


def calendar_categories(subentry: ConfigSubentry) -> frozenset[str]:
    """Return the enabled categories for a calendar subentry."""
    return frozenset(subentry.data.get(CONF_CATEGORIES, DEFAULT_CATEGORIES))
