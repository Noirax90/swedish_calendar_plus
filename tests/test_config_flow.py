"""Tests for the Swedish Calendar Plus config flow."""

from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.swedish_calendar_plus import async_migrate_entry
from custom_components.swedish_calendar_plus.const import (
    CALENDAR_EVE_OPTIONS,
    CATEGORY_HOLIDAYS,
    CATEGORY_NAME_DAYS,
    CONF_CALENDAR_NAME,
    CONF_CATEGORIES,
    CONF_INCLUDE_BRIDGE_DAYS,
    CONF_INCLUDE_SUNDAYS,
    CONF_LANGUAGE,
    CONF_OVERRIDE_SHARED_EVE_SETTINGS,
    CONF_RED_DAY_BRIDGE_DAYS,
    DOMAIN,
    RED_DAY_EVE_OPTIONS,
    SECTION_ADVANCED,
    SUBENTRY_TYPE_CALENDAR,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


def _advanced_defaults(**values: bool) -> dict[str, bool]:
    return {option: values.get(option, False) for option in RED_DAY_EVE_OPTIONS}


def _calendar_advanced_defaults(**values: bool) -> dict[str, bool]:
    return {
        CONF_INCLUDE_BRIDGE_DAYS: values.get(CONF_INCLUDE_BRIDGE_DAYS, False),
        **{option: values.get(option, False) for option in CALENDAR_EVE_OPTIONS},
    }


async def test_user_flow_creates_calendar_entry(hass: HomeAssistant) -> None:
    """A user can configure the calendar without credentials or YAML."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_CALENDAR_NAME: "Svenska helgdagar",
            CONF_LANGUAGE: "sv",
            CONF_CATEGORIES: [CATEGORY_HOLIDAYS],
            SECTION_ADVANCED: {
                CONF_INCLUDE_SUNDAYS: False,
                CONF_RED_DAY_BRIDGE_DAYS: False,
                **_advanced_defaults(),
            },
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Swedish Calendar Plus"
    assert result["data"] == {
        CONF_LANGUAGE: "sv",
        CONF_INCLUDE_SUNDAYS: False,
        CONF_RED_DAY_BRIDGE_DAYS: False,
        **_advanced_defaults(),
    }
    entry = result["result"]
    subentries = entry.get_subentries_of_type(SUBENTRY_TYPE_CALENDAR)
    assert len(subentries) == 1
    assert subentries[0].title == "Svenska helgdagar"
    assert subentries[0].data == {
        CONF_LANGUAGE: "sv",
        CONF_CATEGORIES: [CATEGORY_HOLIDAYS],
    }

    await hass.async_block_till_done()
    registry = er.async_get(hass)
    shared_sensors = [
        entity
        for entity in registry.entities.values()
        if entity.config_entry_id == entry.entry_id and entity.domain == "sensor"
    ]
    assert len(shared_sensors) == 4

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_CALENDAR),
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_CALENDAR_NAME: "Namnsdagar",
            CONF_LANGUAGE: "sv",
            CONF_CATEGORIES: [CATEGORY_NAME_DAYS],
            SECTION_ADVANCED: {
                CONF_OVERRIDE_SHARED_EVE_SETTINGS: False,
                **_calendar_advanced_defaults(),
            },
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    assert len(entry.get_subentries_of_type(SUBENTRY_TYPE_CALENDAR)) == 2
    shared_sensors = [
        entity
        for entity in registry.entities.values()
        if entity.config_entry_id == entry.entry_id and entity.domain == "sensor"
    ]
    calendars = [
        entity
        for entity in registry.entities.values()
        if entity.config_entry_id == entry.entry_id and entity.domain == "calendar"
    ]
    assert len(shared_sensors) == 4
    assert len(calendars) == 2


async def test_version_one_entry_migrates_to_calendar_subentry(
    hass: HomeAssistant,
) -> None:
    """Preserve an existing calendar while moving settings to a subentry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Old calendar",
        version=1,
        data={
            CONF_CALENDAR_NAME: "Old calendar",
            CONF_LANGUAGE: "en",
            CONF_INCLUDE_SUNDAYS: False,
        },
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry)
    assert entry.version == 2
    assert entry.data == {
        CONF_LANGUAGE: "en",
        CONF_INCLUDE_SUNDAYS: False,
    }
    subentries = entry.get_subentries_of_type(SUBENTRY_TYPE_CALENDAR)
    assert len(subentries) == 1
    assert subentries[0].title == "Old calendar"
    assert subentries[0].data[CONF_CATEGORIES] == [CATEGORY_HOLIDAYS]


async def test_advanced_options_section_is_collapsed(hass: HomeAssistant) -> None:
    """Advanced shared settings are grouped without changing stored options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_LANGUAGE: "sv",
            CONF_INCLUDE_SUNDAYS: True,
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    advanced = result["data_schema"].schema[vol.Required(SECTION_ADVANCED)]
    assert advanced.options["collapsed"] is True

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_LANGUAGE: "en",
            SECTION_ADVANCED: {
                CONF_INCLUDE_SUNDAYS: False,
                CONF_RED_DAY_BRIDGE_DAYS: False,
                **_advanced_defaults(),
            },
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {
        CONF_LANGUAGE: "en",
        CONF_INCLUDE_SUNDAYS: False,
        CONF_RED_DAY_BRIDGE_DAYS: False,
        **_advanced_defaults(),
    }
