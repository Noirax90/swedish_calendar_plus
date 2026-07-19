"""Shared entity helpers for Swedish Calendar Plus."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.core import callback
from homeassistant.helpers.event import async_track_time_change

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import SwedishHolidayCalendarConfigEntry


class DailyEntityMixin:
    """Refresh an entity when Home Assistant's local date changes."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry: SwedishHolidayCalendarConfigEntry,
        key: str,
    ) -> None:
        """Initialize a daily entity with a stable unique ID."""
        self._hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"

    async def async_added_to_hass(self) -> None:
        """Schedule a state refresh at local midnight."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_track_time_change(
                self._hass,
                self._handle_midnight,
                hour=0,
                minute=0,
                second=0,
            )
        )

    @callback
    def _handle_midnight(self, *_: object) -> None:
        """Write state from the Home Assistant event loop at midnight."""
        self.async_write_ha_state()
