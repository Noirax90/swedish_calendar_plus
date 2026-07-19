"""Tests for integration diagnostics."""

from types import SimpleNamespace

from homeassistant.config_entries import ConfigSubentryData
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.swedish_calendar_plus.const import (
    DOMAIN,
    SUBENTRY_TYPE_CALENDAR,
)
from custom_components.swedish_calendar_plus.diagnostics import (
    async_get_config_entry_diagnostics,
)


async def test_diagnostics_exclude_complete_source_datasets(hass) -> None:  # noqa: ANN001
    """Diagnostics expose provenance and failures but not thousands of records."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"language": "sv"},
        options={"include_sundays": True},
        subentries_data=[
            ConfigSubentryData(
                data={"categories": ["holidays"]},
                subentry_type=SUBENTRY_TYPE_CALENDAR,
                title="Calendar",
                unique_id=None,
            )
        ],
    )
    entry.runtime_data = SimpleNamespace(
        data={
            "last_successful_update": "2026-07-19T12:00:00+00:00",
            "consecutive_failures": 0,
            "name_days_metadata": {"record_count": 630},
            "name_days": {"days": ["must not be included"]},
        }
    )

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["source_update"] == {
        "last_successful_update": "2026-07-19T12:00:00+00:00",
        "last_update_error": None,
        "consecutive_failures": 0,
        "name_days": {"record_count": 630},
        "theme_days": None,
    }
    assert "must not be included" not in str(result)
