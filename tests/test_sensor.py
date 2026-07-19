"""Tests for shared date-related sensors."""

from datetime import UTC, date, datetime
from typing import TYPE_CHECKING
from unittest.mock import patch
from zoneinfo import ZoneInfo

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.swedish_calendar_plus.binary_sensor import (
    BridgeDayBinarySensor,
    FlagDayBinarySensor,
    PublicHolidayBinarySensor,
    RedDayBinarySensor,
    WorkdayBinarySensor,
)
from custom_components.swedish_calendar_plus.const import DOMAIN
from custom_components.swedish_calendar_plus.sensor import (
    DaysUntilNextPublicHolidaySensor,
    NextPublicHolidaySensor,
    WeekNumberSensor,
    _DailySensor,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


def test_next_holiday_sensors_respect_red_day_eves(hass: HomeAssistant) -> None:
    """A holiday eve configured as red is considered by both next sensors."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"red_day_all_hallows_eve": True},
    )
    next_holiday = NextPublicHolidaySensor(hass, entry)
    days_until = DaysUntilNextPublicHolidaySensor(hass, entry)

    with patch.object(_DailySensor, "_today", return_value=date(2026, 10, 29)):
        assert next_holiday.native_value == date(2026, 10, 30)
        assert next_holiday.extra_state_attributes == {
            "holiday": "Allhelgonaafton",
            "holiday_key": "all_hallows_eve",
            "red_day_type": "holiday_eve",
        }
        assert days_until.native_value == 1


def test_next_holiday_sensors_respect_red_bridge_days(hass: HomeAssistant) -> None:
    """A bridge day configured as red is considered by both next sensors."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"red_day_bridge_days": True},
    )
    next_holiday = NextPublicHolidaySensor(hass, entry)
    days_until = DaysUntilNextPublicHolidaySensor(hass, entry)

    with patch.object(_DailySensor, "_today", return_value=date(2026, 5, 15)):
        assert next_holiday.native_value == date(2026, 5, 15)
        assert next_holiday.extra_state_attributes == {
            "holiday": "Klämdag",
            "holiday_key": "bridge_day",
            "red_day_type": "bridge_day",
        }
        assert days_until.native_value == 0


def test_red_day_sensor_explains_why_today_is_red(hass: HomeAssistant) -> None:
    """The red-day sensor exposes a stable type, key, and localized name."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"red_day_christmas_eve": True},
    )
    sensor = RedDayBinarySensor(hass, entry)

    with patch(
        "custom_components.swedish_calendar_plus.binary_sensor.dt_util.now",
        return_value=datetime(2026, 12, 24, 12, tzinfo=UTC),
    ):
        assert sensor.is_on
        assert sensor.extra_state_attributes == {
            "red_day_type": "holiday_eve",
            "red_day_key": "christmas_eve",
            "red_day_name": "Julafton",
        }


def test_public_holiday_bridge_day_and_workday_sensors(hass: HomeAssistant) -> None:
    """Independent day-type sensors follow their documented definitions."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"red_day_bridge_days": True},
    )
    public_holiday = PublicHolidayBinarySensor(hass, entry)
    bridge_day = BridgeDayBinarySensor(hass, entry)
    workday = WorkdayBinarySensor(hass, entry)

    with patch(
        "custom_components.swedish_calendar_plus.binary_sensor.dt_util.now",
        return_value=datetime(2026, 5, 15, 12, tzinfo=UTC),
    ):
        assert not public_holiday.is_on
        assert bridge_day.is_on
        assert not workday.is_on

    with patch(
        "custom_components.swedish_calendar_plus.binary_sensor.dt_util.now",
        return_value=datetime(2026, 6, 6, 12, tzinfo=UTC),
    ):
        assert public_holiday.is_on
        assert not workday.is_on

    with patch(
        "custom_components.swedish_calendar_plus.binary_sensor.dt_util.now",
        return_value=datetime(2026, 6, 8, 12, tzinfo=UTC),
    ):
        assert workday.is_on


def test_flag_day_sensor_is_informational(hass: HomeAssistant) -> None:
    """Flag-day state and attributes do not depend on red-day settings."""
    entry = MockConfigEntry(domain=DOMAIN, data={"language": "en"})
    sensor = FlagDayBinarySensor(hass, entry)

    with patch(
        "custom_components.swedish_calendar_plus.binary_sensor.dt_util.now",
        return_value=datetime(2026, 1, 28, 12, tzinfo=UTC),
    ):
        assert sensor.is_on
        assert sensor.extra_state_attributes == {
            "flag_day_key": "flag_kings_name_day",
            "flag_day_name": "King Carl XVI Gustaf's name day",
        }

    with patch(
        "custom_components.swedish_calendar_plus.binary_sensor.dt_util.now",
        return_value=datetime(2026, 1, 29, 12, tzinfo=UTC),
    ):
        assert not sensor.is_on
        assert sensor.extra_state_attributes == {}


def test_daily_sensors_use_home_assistant_local_date(hass: HomeAssistant) -> None:
    """The local date wins when Stockholm has crossed midnight before UTC."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    sensor = WeekNumberSensor(hass, entry)
    stockholm_time = datetime(2026, 1, 1, 23, 30, tzinfo=UTC).astimezone(
        ZoneInfo("Europe/Stockholm")
    )

    with patch(
        "custom_components.swedish_calendar_plus.sensor.dt_util.now",
        return_value=stockholm_time,
    ):
        assert sensor._today() == date(2026, 1, 2)
