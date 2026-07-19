"""Config and calendar-subentry flows for Swedish Calendar Plus."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant import config_entries

from .config_schema import (
    calendar_schema,
    flatten_advanced,
    initial_schema,
    options_schema,
    shared_eve_defaults,
)
from .const import (
    CONF_CALENDAR_NAME,
    CONF_CATEGORIES,
    CONF_INCLUDE_SUNDAYS,
    CONF_LANGUAGE,
    CONF_OVERRIDE_SHARED_EVE_SETTINGS,
    CONF_RED_DAY_BRIDGE_DAYS,
    DEFAULT_CATEGORIES,
    DEFAULT_LANGUAGE,
    DOMAIN,
    INTEGRATION_NAME,
    RED_DAY_EVE_OPTIONS,
    SUBENTRY_TYPE_CALENDAR,
)

if TYPE_CHECKING:
    from homeassistant.data_entry_flow import FlowResult

SOURCE_DESCRIPTION_PLACEHOLDERS = {
    "name_day_source": "https://www.svenskaakademien.se/svenska-akademien/almanackan",
    "theme_day_source": "https://temadagar.se/kalender/",
}


class SwedishHolidayCalendarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle integration setup and calendar subentries."""

    VERSION = 2

    async def async_step_user(
        self,
        user_input: dict[str, object] | None = None,
    ) -> FlowResult:
        """Create the integration and its first calendar."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            flatten_advanced(user_input)
            calendar_name = str(user_input[CONF_CALENDAR_NAME])
            language = user_input[CONF_LANGUAGE]
            categories = user_input[CONF_CATEGORIES]
            return self.async_create_entry(
                title=INTEGRATION_NAME,
                data={
                    CONF_LANGUAGE: language,
                    CONF_INCLUDE_SUNDAYS: user_input[CONF_INCLUDE_SUNDAYS],
                    CONF_RED_DAY_BRIDGE_DAYS: user_input[CONF_RED_DAY_BRIDGE_DAYS],
                    **{key: user_input[key] for key in RED_DAY_EVE_OPTIONS},
                },
                subentries=[
                    config_entries.ConfigSubentryData(
                        data={
                            CONF_LANGUAGE: language,
                            CONF_CATEGORIES: categories,
                        },
                        subentry_type=SUBENTRY_TYPE_CALENDAR,
                        title=calendar_name,
                        unique_id=None,
                    )
                ],
            )

        return self.async_show_form(
            step_id="user",
            data_schema=initial_schema(),
            description_placeholders=SOURCE_DESCRIPTION_PLACEHOLDERS,
        )

    @classmethod
    def async_get_supported_subentry_types(
        cls,
        _config_entry: config_entries.ConfigEntry,
    ) -> dict[str, type[config_entries.ConfigSubentryFlow]]:
        """Return supported subentry flow handlers."""
        return {SUBENTRY_TYPE_CALENDAR: CalendarSubentryFlow}

    @staticmethod
    def async_get_options_flow(
        _config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return global integration options."""
        return SwedishHolidayCalendarOptionsFlow()


class CalendarSubentryFlow(config_entries.ConfigSubentryFlow):
    """Add or reconfigure a filtered calendar."""

    async def async_step_user(
        self,
        user_input: dict[str, object] | None = None,
    ) -> config_entries.SubentryFlowResult:
        """Add a calendar."""
        if user_input is not None:
            flatten_advanced(user_input)
            title = str(user_input.pop(CONF_CALENDAR_NAME))
            return self.async_create_entry(title=title, data=user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=calendar_schema(shared_eve_defaults(self._get_entry())),
            description_placeholders=SOURCE_DESCRIPTION_PLACEHOLDERS,
        )

    async def async_step_reconfigure(
        self,
        user_input: dict[str, object] | None = None,
    ) -> config_entries.SubentryFlowResult:
        """Reconfigure a calendar."""
        entry = self._get_entry()
        subentry = self._get_reconfigure_subentry()
        if user_input is not None:
            flatten_advanced(user_input)
            title = str(user_input.pop(CONF_CALENDAR_NAME))
            return self.async_update_and_abort(
                entry,
                subentry,
                title=title,
                data=user_input,
            )
        defaults = (
            dict(subentry.data)
            if subentry.data.get(CONF_OVERRIDE_SHARED_EVE_SETTINGS, False)
            else shared_eve_defaults(entry)
        )
        defaults[CONF_OVERRIDE_SHARED_EVE_SETTINGS] = subentry.data.get(
            CONF_OVERRIDE_SHARED_EVE_SETTINGS, False
        )
        defaults.update(
            {
                CONF_LANGUAGE: subentry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
                CONF_CATEGORIES: subentry.data.get(
                    CONF_CATEGORIES, list(DEFAULT_CATEGORIES)
                ),
            }
        )
        defaults[CONF_CALENDAR_NAME] = subentry.title
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=calendar_schema(defaults),
            description_placeholders=SOURCE_DESCRIPTION_PLACEHOLDERS,
        )


class SwedishHolidayCalendarOptionsFlow(config_entries.OptionsFlow):
    """Manage settings shared by all calendars and sensors."""

    async def async_step_init(
        self,
        user_input: dict[str, object] | None = None,
    ) -> FlowResult:
        """Manage global options."""
        if user_input is not None:
            return self.async_create_entry(data=flatten_advanced(user_input))

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema(self.config_entry),
        )
