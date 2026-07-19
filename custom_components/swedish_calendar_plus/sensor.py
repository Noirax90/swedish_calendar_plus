"""Sensors for Swedish Calendar Plus."""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.util import dt as dt_util

from .data import day_policy, sensor_language
from .entity import DailyEntityMixin
from .holidays import SwedishHoliday, holidays_between, red_day_type

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .data import SwedishHolidayCalendarConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SwedishHolidayCalendarConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up date-related sensors."""
    async_add_entities(
        [
            WeekNumberSensor(hass, entry),
            NamesTodaySensor(hass, entry),
            NextPublicHolidaySensor(hass, entry),
            DaysUntilNextPublicHolidaySensor(hass, entry),
        ]
    )


class _DailySensor(DailyEntityMixin, SensorEntity):
    """Base sensor that refreshes when the local date changes."""

    @staticmethod
    def _today() -> date:
        return dt_util.now().date()

    def _next_red_day(self) -> SwedishHoliday | None:
        today = self._today()
        policy = day_policy(self._entry)
        holidays = holidays_between(
            today,
            today + timedelta(days=400),
            include_sundays=False,
            red_day_eves=policy.red_day_eves,
            include_bridge_days=policy.include_bridge_days,
        )
        return holidays[0] if holidays else None


class WeekNumberSensor(_DailySensor):
    """Current ISO week number."""

    _attr_icon = "mdi:calendar-week"
    _attr_translation_key = "week_number"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: SwedishHolidayCalendarConfigEntry,
    ) -> None:
        """Initialize the week-number sensor."""
        super().__init__(hass, entry, "week_number")

    @property
    def native_value(self) -> int:
        """Return the current ISO week number."""
        return self._today().isocalendar().week


class NamesTodaySensor(_DailySensor):
    """Names celebrated today."""

    _attr_icon = "mdi:party-popper"
    _attr_translation_key = "names_today"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: SwedishHolidayCalendarConfigEntry,
    ) -> None:
        """Initialize the names-today sensor."""
        super().__init__(hass, entry, "names_today")

    @property
    def native_value(self) -> str | None:
        """Return names celebrated today."""
        today = self._today()
        item = next(
            (
                item
                for item in self._entry.runtime_data.sources.name_days_for_year(
                    today.year
                )
                if item.date == today
            ),
            None,
        )
        return ", ".join(item.names) if item else None


class NextPublicHolidaySensor(_DailySensor):
    """Date of the next configured red day."""

    _attr_device_class = SensorDeviceClass.DATE
    _attr_icon = "mdi:calendar-arrow-right"
    _attr_translation_key = "next_public_holiday"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: SwedishHolidayCalendarConfigEntry,
    ) -> None:
        """Initialize the next-holiday sensor."""
        super().__init__(hass, entry, "next_public_holiday")

    @property
    def native_value(self) -> date | None:
        """Return the date of the next named holiday, including today."""
        holiday = self._next_red_day()
        return holiday.date if holiday else None

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return the localized holiday name and stable key."""
        holiday = self._next_red_day()
        if holiday is None:
            return {}
        return {
            "holiday": holiday.localized_name(sensor_language(self._entry)),
            "holiday_key": holiday.key,
            "red_day_type": red_day_type(holiday.key),
        }


class DaysUntilNextPublicHolidaySensor(_DailySensor):
    """Days remaining until the next configured red day."""

    _attr_icon = "mdi:calendar-clock"
    _attr_native_unit_of_measurement = "d"
    _attr_translation_key = "days_until_next_public_holiday"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: SwedishHolidayCalendarConfigEntry,
    ) -> None:
        """Initialize the days-until sensor."""
        super().__init__(hass, entry, "days_until_next_public_holiday")

    @property
    def native_value(self) -> int | None:
        """Return days until the next named holiday, where today is zero."""
        holiday = self._next_red_day()
        return (holiday.date - self._today()).days if holiday else None
