"""Tests for integration setup lifecycle."""

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.swedish_calendar_plus import async_setup_entry
from custom_components.swedish_calendar_plus.const import DOMAIN
from custom_components.swedish_calendar_plus.sources import load_sources

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


async def test_static_sources_are_loaded_via_executor(hass: HomeAssistant) -> None:
    """Bundled JSON must be read before entities run and outside the event loop."""
    entry = MockConfigEntry(domain=DOMAIN, title="Swedish Calendar Plus", data={})
    entry.add_to_hass(hass)

    with (
        patch.object(hass, "async_add_executor_job", AsyncMock()) as executor_job,
        patch.object(
            hass.config_entries,
            "async_forward_entry_setups",
            AsyncMock(),
        ),
    ):
        assert await async_setup_entry(hass, entry)

    executor_job.assert_awaited_once_with(load_sources)
