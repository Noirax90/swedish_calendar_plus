"""Binary sensors for Swedish Calendar Plus."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.util import dt as dt_util

from .data import (
    day_policy,
    sensor_language,
)
from .entity import DailyEntityMixin
from .flag_days import SwedishFlagDay, flag_days_for_year
from .holidays import DayClassification, classify_day
from .localization import translate

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .data import SwedishHolidayCalendarConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SwedishHolidayCalendarConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up red-day binary sensors."""
    async_add_entities(
        [
            RedDayBinarySensor(hass, entry),
            PublicHolidayBinarySensor(hass, entry),
            HolidayEveBinarySensor(hass, entry),
            BridgeDayBinarySensor(hass, entry),
            WorkdayBinarySensor(hass, entry),
            FlagDayBinarySensor(hass, entry),
        ]
    )


class _DailyBinarySensor(DailyEntityMixin, BinarySensorEntity):
    """Base class for a binary sensor derived from the local date."""

    def _classification(self) -> DayClassification:
        """Classify today once using the shared red-day policy."""
        return classify_day(dt_util.now().date(), day_policy(self._entry))


class RedDayBinarySensor(_DailyBinarySensor):
    """Whether today is a red day under the configured policy."""

    _attr_icon = "mdi:calendar-alert"
    _attr_translation_key = "red_day"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: SwedishHolidayCalendarConfigEntry,
    ) -> None:
        """Initialize the red-day sensor."""
        super().__init__(hass, entry, "red_day")

    @property
    def is_on(self) -> bool:
        """Return whether today counts as a red day."""
        return self._classification().is_red_day

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return why today is red using stable machine-readable values."""
        classification = self._classification()
        if not classification.is_red_day:
            return {}
        language = sensor_language(self._entry)
        key = classification.red_day_key
        if classification.public_holiday is not None:
            name = classification.public_holiday.localized_name(language)
        elif classification.holiday_eve is not None:
            name = classification.holiday_eve.localized_name(language)
        else:
            name = translate(language, f"events.{key}")
        return {
            "red_day_type": classification.red_day_type,
            "red_day_key": key,
            "red_day_name": name,
        }


class HolidayEveBinarySensor(_DailyBinarySensor):
    """Whether today is an established Swedish holiday eve."""

    _attr_icon = "mdi:weather-sunset"
    _attr_translation_key = "holiday_eve"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: SwedishHolidayCalendarConfigEntry,
    ) -> None:
        """Initialize the holiday-eve sensor."""
        super().__init__(hass, entry, "holiday_eve")

    @property
    def is_on(self) -> bool:
        """Return whether today is a configured holiday eve."""
        return self._classification().is_holiday_eve

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return the localized eve name and stable key."""
        item = self._classification().holiday_eve
        if item is None:
            return {}
        return {
            "holiday_eve": item.localized_name(sensor_language(self._entry)),
            "holiday_eve_key": item.key,
        }


class PublicHolidayBinarySensor(_DailyBinarySensor):
    """Whether today is a named legal Swedish public holiday."""

    _attr_icon = "mdi:calendar-star"
    _attr_translation_key = "public_holiday"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: SwedishHolidayCalendarConfigEntry,
    ) -> None:
        """Initialize the public-holiday sensor."""
        super().__init__(hass, entry, "public_holiday")

    @property
    def is_on(self) -> bool:
        """Return whether today is a named legal public holiday."""
        return self._classification().is_public_holiday

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return the stable key and localized public-holiday name."""
        holiday = self._classification().public_holiday
        if holiday is None:
            return {}
        return {
            "holiday_key": holiday.key,
            "holiday_name": holiday.localized_name(sensor_language(self._entry)),
        }


class BridgeDayBinarySensor(_DailyBinarySensor):
    """Whether today is a bridge day regardless of its red-day policy."""

    _attr_icon = "mdi:calendar-expand-horizontal"
    _attr_translation_key = "bridge_day"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: SwedishHolidayCalendarConfigEntry,
    ) -> None:
        """Initialize the bridge-day sensor."""
        super().__init__(hass, entry, "bridge_day")

    @property
    def is_on(self) -> bool:
        """Return whether today lies between two days off."""
        return self._classification().is_bridge_day


class WorkdayBinarySensor(_DailyBinarySensor):
    """Whether today is a standard five-day-week workday."""

    _attr_icon = "mdi:briefcase-outline"
    _attr_translation_key = "workday"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: SwedishHolidayCalendarConfigEntry,
    ) -> None:
        """Initialize the workday sensor."""
        super().__init__(hass, entry, "workday")

    @property
    def is_on(self) -> bool:
        """Return whether today is Monday-Friday and not configured red."""
        return self._classification().is_workday


class FlagDayBinarySensor(_DailyBinarySensor):
    """Whether today is an official Swedish flag day."""

    _attr_icon = "mdi:flag"
    _attr_translation_key = "flag_day"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: SwedishHolidayCalendarConfigEntry,
    ) -> None:
        """Initialize the flag-day sensor."""
        super().__init__(hass, entry, "flag_day")

    def _flag_day(self) -> SwedishFlagDay | None:
        """Return today's official flag day, if any."""
        today = dt_util.now().date()
        return next(
            (item for item in flag_days_for_year(today.year) if item.date == today),
            None,
        )

    @property
    def is_on(self) -> bool:
        """Return whether today is an official Swedish flag day."""
        return self._flag_day() is not None

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return the stable key and localized flag-day name."""
        flag_day = self._flag_day()
        if flag_day is None:
            return {}
        return {
            "flag_day_key": flag_day.key,
            "flag_day_name": flag_day.localized_name(sensor_language(self._entry)),
        }
