"""Filtered Swedish calendar entities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import TYPE_CHECKING

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.util import dt as dt_util

from .const import (
    CATEGORY_FLAG_DAYS,
    CATEGORY_HOLIDAY_EVES,
    CATEGORY_HOLIDAYS,
    CATEGORY_NAME_DAYS,
    CATEGORY_THEME_DAYS,
    SUBENTRY_TYPE_CALENDAR,
)
from .data import (
    calendar_categories,
    calendar_included_eves,
    calendar_includes_bridge_days,
    calendar_language,
    include_sundays,
)
from .flag_days import flag_days_for_year
from .holidays import DayPolicy, classify_day, holiday_eves_for_year, holidays_between
from .localization import translate

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigSubentry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .data import SwedishHolidayCalendarConfigEntry


@dataclass(frozen=True, slots=True)
class _CalendarItem:
    date: date
    summary: str
    description: str | None = None


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: SwedishHolidayCalendarConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up all configured calendar subentries."""
    async_add_entities(
        SwedishFilteredCalendar(entry, subentry)
        for subentry in entry.get_subentries_of_type(SUBENTRY_TYPE_CALENDAR)
    )


def _items_between(
    entry: SwedishHolidayCalendarConfigEntry,
    subentry: ConfigSubentry,
    start: date,
    end: date,
) -> tuple[_CalendarItem, ...]:
    language = calendar_language(subentry)
    categories = calendar_categories(subentry)
    items: list[_CalendarItem] = []

    if CATEGORY_HOLIDAYS in categories:
        items.extend(
            _CalendarItem(holiday.date, holiday.localized_name(language))
            for holiday in holidays_between(
                start,
                end,
                include_sundays=include_sundays(entry),
            )
        )

    included_eves = calendar_included_eves(entry, subentry)
    for year in range(start.year, end.year + 1):
        items.extend(
            _CalendarItem(item.date, item.localized_name(language))
            for item in holiday_eves_for_year(year)
            if item.key in included_eves and start <= item.date < end
        )
        if calendar_includes_bridge_days(subentry):
            current = max(start, date(year, 1, 1))
            year_end = min(end, date(year + 1, 1, 1))
            while current < year_end:
                if classify_day(
                    current, DayPolicy(red_day_eves=included_eves)
                ).is_bridge_day:
                    items.append(
                        _CalendarItem(current, translate(language, "event_bridge_day"))
                    )
                current += timedelta(days=1)
        if CATEGORY_HOLIDAY_EVES in categories:
            items.extend(
                _CalendarItem(item.date, item.localized_name(language))
                for item in holiday_eves_for_year(year)
                if start <= item.date < end and item.key not in included_eves
            )
        if CATEGORY_NAME_DAYS in categories:
            items.extend(
                _CalendarItem(item.date, ", ".join(item.names))
                for item in entry.runtime_data.sources.name_days_for_year(year)
                if start <= item.date < end
            )
        if CATEGORY_FLAG_DAYS in categories:
            items.extend(
                _CalendarItem(item.date, item.localized_name(language))
                for item in flag_days_for_year(year)
                if start <= item.date < end
            )
        if CATEGORY_THEME_DAYS in categories:
            attribution = translate(language, "theme_attribution")
            items.extend(
                _CalendarItem(
                    item.date,
                    item.title,
                    f"{attribution}: {item.url}",
                )
                for item in entry.runtime_data.sources.theme_days_for_year(year)
                if start <= item.date < end
            )

    return tuple(sorted(items, key=lambda item: (item.date, item.summary)))


class SwedishFilteredCalendar(CalendarEntity):
    """A user-configured filtered Swedish calendar."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:calendar-star"

    def __init__(
        self,
        entry: SwedishHolidayCalendarConfigEntry,
        subentry: ConfigSubentry,
    ) -> None:
        """Initialize a filtered calendar subentry entity."""
        self._entry = entry
        self._subentry = subentry
        self._attr_name = subentry.title
        self._attr_unique_id = f"{entry.entry_id}_{subentry.subentry_id}"

    @staticmethod
    def _as_event(item: _CalendarItem) -> CalendarEvent:
        return CalendarEvent(
            start=item.date,
            end=item.date + timedelta(days=1),
            summary=item.summary,
            description=item.description,
        )

    @property
    def event(self) -> CalendarEvent | None:
        """Return the active or next upcoming event."""
        today = dt_util.now().date()
        items = _items_between(
            self._entry,
            self._subentry,
            today,
            today + timedelta(days=400),
        )
        return self._as_event(items[0]) if items else None

    async def async_get_events(
        self,
        hass: HomeAssistant,  # noqa: ARG002
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return configured events overlapping the requested range."""
        start = start_date.date()
        end = end_date.date()
        if end_date.timetz().replace(tzinfo=None) != time.min:
            end += timedelta(days=1)
        return [
            self._as_event(item)
            for item in _items_between(self._entry, self._subentry, start, end)
        ]
