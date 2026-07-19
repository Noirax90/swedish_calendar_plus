"""Schemas and form-data helpers for integration config flows."""

from __future__ import annotations

from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant.data_entry_flow import section
from homeassistant.helpers import selector

from .const import (
    CALENDAR_CATEGORIES,
    CALENDAR_EVE_OPTIONS,
    CONF_CALENDAR_NAME,
    CONF_CATEGORIES,
    CONF_INCLUDE_BRIDGE_DAYS,
    CONF_INCLUDE_SUNDAYS,
    CONF_LANGUAGE,
    CONF_OVERRIDE_SHARED_EVE_SETTINGS,
    CONF_RED_DAY_BRIDGE_DAYS,
    DEFAULT_CALENDAR_NAME,
    DEFAULT_CATEGORIES,
    DEFAULT_INCLUDE_SUNDAYS,
    DEFAULT_LANGUAGE,
    RED_DAY_EVE_OPTIONS,
    SECTION_ADVANCED,
    SUPPORTED_LANGUAGES,
)

if TYPE_CHECKING:
    from homeassistant import config_entries


def _language_selector() -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=list(SUPPORTED_LANGUAGES),
            mode=selector.SelectSelectorMode.DROPDOWN,
            translation_key="language",
        )
    )


def _category_selector() -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=list(CALENDAR_CATEGORIES),
            multiple=True,
            translation_key="calendar_category",
        )
    )


def advanced_schema(
    defaults: dict[str, object],
    *,
    include_sundays: bool,
    include_override: bool,
) -> section:
    """Build the collapsed advanced section shared by the forms."""
    fields: dict[vol.Marker, selector.BooleanSelector] = {}
    if include_override:
        fields[
            vol.Required(
                CONF_OVERRIDE_SHARED_EVE_SETTINGS,
                default=defaults.get(CONF_OVERRIDE_SHARED_EVE_SETTINGS, False),
            )
        ] = selector.BooleanSelector()
        fields[
            vol.Required(
                CONF_INCLUDE_BRIDGE_DAYS,
                default=defaults.get(CONF_INCLUDE_BRIDGE_DAYS, False),
            )
        ] = selector.BooleanSelector()
    if include_sundays:
        fields[
            vol.Required(
                CONF_INCLUDE_SUNDAYS,
                default=defaults.get(CONF_INCLUDE_SUNDAYS, DEFAULT_INCLUDE_SUNDAYS),
            )
        ] = selector.BooleanSelector()
        fields[
            vol.Required(
                CONF_RED_DAY_BRIDGE_DAYS,
                default=defaults.get(CONF_RED_DAY_BRIDGE_DAYS, False),
            )
        ] = selector.BooleanSelector()
    options = CALENDAR_EVE_OPTIONS if include_override else RED_DAY_EVE_OPTIONS
    for option in options:
        fields[vol.Required(option, default=defaults.get(option, False))] = (
            selector.BooleanSelector()
        )
    return section(vol.Schema(fields), {"collapsed": True})


def flatten_advanced(user_input: dict[str, object]) -> dict[str, object]:
    """Flatten section data before storing it in a config entry or subentry."""
    advanced = user_input.pop(SECTION_ADVANCED)
    user_input.update(advanced)
    return user_input


def shared_eve_defaults(entry: config_entries.ConfigEntry) -> dict[str, object]:
    """Return shared holiday-eve settings as calendar form defaults."""
    return {
        f"include_{key.removeprefix('red_day_')}": entry.options.get(
            key, entry.data.get(key, False)
        )
        for key in RED_DAY_EVE_OPTIONS
    }


def initial_schema() -> vol.Schema:
    """Build the initial integration and first-calendar schema."""
    return vol.Schema(
        {
            vol.Required(
                CONF_CALENDAR_NAME, default=DEFAULT_CALENDAR_NAME
            ): selector.TextSelector(),
            vol.Required(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): _language_selector(),
            vol.Required(
                CONF_CATEGORIES, default=list(DEFAULT_CATEGORIES)
            ): _category_selector(),
            vol.Required(SECTION_ADVANCED): advanced_schema(
                {}, include_sundays=True, include_override=False
            ),
        }
    )


def calendar_schema(defaults: dict[str, object]) -> vol.Schema:
    """Build a calendar add or reconfigure schema."""
    return vol.Schema(
        {
            vol.Required(
                CONF_CALENDAR_NAME,
                default=defaults.get(CONF_CALENDAR_NAME, DEFAULT_CALENDAR_NAME),
            ): selector.TextSelector(),
            vol.Required(
                CONF_LANGUAGE,
                default=defaults.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
            ): _language_selector(),
            vol.Required(
                CONF_CATEGORIES,
                default=defaults.get(CONF_CATEGORIES, list(DEFAULT_CATEGORIES)),
            ): _category_selector(),
            vol.Required(SECTION_ADVANCED): advanced_schema(
                defaults, include_sundays=False, include_override=True
            ),
        }
    )


def options_schema(entry: config_entries.ConfigEntry) -> vol.Schema:
    """Build the schema for settings shared by calendars and sensors."""
    defaults = {
        key: entry.options.get(key, entry.data.get(key, False))
        for key in RED_DAY_EVE_OPTIONS
    } | {
        CONF_INCLUDE_SUNDAYS: entry.options.get(
            CONF_INCLUDE_SUNDAYS,
            entry.data.get(CONF_INCLUDE_SUNDAYS, DEFAULT_INCLUDE_SUNDAYS),
        ),
        CONF_RED_DAY_BRIDGE_DAYS: entry.options.get(
            CONF_RED_DAY_BRIDGE_DAYS,
            entry.data.get(CONF_RED_DAY_BRIDGE_DAYS, False),
        ),
    }
    return vol.Schema(
        {
            vol.Required(
                CONF_LANGUAGE,
                default=entry.options.get(
                    CONF_LANGUAGE,
                    entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
                ),
            ): _language_selector(),
            vol.Required(SECTION_ADVANCED): advanced_schema(
                defaults, include_sundays=True, include_override=False
            ),
        }
    )
