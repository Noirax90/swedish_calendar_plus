"""Thread-safety regression tests for scheduled entity callbacks."""

from homeassistant.core import is_callback

from custom_components.swedish_calendar_plus.binary_sensor import (
    HolidayEveBinarySensor,
    RedDayBinarySensor,
)
from custom_components.swedish_calendar_plus.sensor import _DailySensor


def test_midnight_handlers_are_event_loop_callbacks() -> None:
    """Midnight state writes must never be dispatched to an executor thread."""
    assert is_callback(RedDayBinarySensor._handle_midnight)
    assert is_callback(HolidayEveBinarySensor._handle_midnight)
    assert is_callback(_DailySensor._handle_midnight)
