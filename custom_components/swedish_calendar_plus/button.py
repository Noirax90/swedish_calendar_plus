"""Manual source update button."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .data import SwedishHolidayCalendarConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: SwedishHolidayCalendarConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the source update button."""
    async_add_entities([UpdateSourcesButton(entry)])


class UpdateSourcesButton(ButtonEntity):
    """Download and activate the latest validated source datasets."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:database-sync"
    _attr_translation_key = "update_sources"

    def __init__(self, entry: SwedishHolidayCalendarConfigEntry) -> None:
        """Initialize the source update button."""
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_update_sources"

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return the timestamp of the latest fully successful update."""
        timestamp = self._entry.runtime_data.data.get("last_successful_update")
        return {"last_successful_update": timestamp} if timestamp else {}

    async def async_press(self) -> None:
        """Refresh both runtime datasets."""
        changed = await self._entry.runtime_data.async_refresh()
        self.async_write_ha_state()
        if changed:
            self.hass.async_create_task(
                self.hass.config_entries.async_reload(self._entry.entry_id),
                "reload Swedish Calendar Plus after source update",
            )
