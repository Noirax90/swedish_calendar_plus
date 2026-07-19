"""Shared Home Assistant test fixtures."""

import pytest

from custom_components.swedish_calendar_plus.localization import load_translations


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: None,
) -> None:
    """Enable loading custom integrations in every test."""
    del enable_custom_integrations
    load_translations()
