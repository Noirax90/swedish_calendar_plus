"""Tests for the manual source update button."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.swedish_calendar_plus.button import UpdateSourcesButton
from custom_components.swedish_calendar_plus.const import DOMAIN


def test_update_button_exposes_last_successful_update() -> None:
    """The persisted successful-update timestamp is visible on the button."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.runtime_data = SimpleNamespace(
        data={"last_successful_update": "2026-07-19T12:34:56+00:00"}
    )

    button = UpdateSourcesButton(entry)

    assert button.extra_state_attributes == {
        "last_successful_update": "2026-07-19T12:34:56+00:00"
    }


async def test_unchanged_update_does_not_reload_integration(hass) -> None:  # noqa: ANN001
    """A successful fetch with identical fingerprints only updates the button."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.runtime_data = SimpleNamespace(
        data={},
        async_refresh=AsyncMock(return_value=False),
    )
    button = UpdateSourcesButton(entry)
    button.hass = hass

    with (
        patch.object(button, "async_write_ha_state") as write_state,
        patch.object(hass, "async_create_task") as create_task,
    ):
        await button.async_press()

    write_state.assert_called_once_with()
    create_task.assert_not_called()
