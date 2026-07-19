"""Constants for Swedish Calendar Plus."""

from typing import Final

DOMAIN = "swedish_calendar_plus"
INTEGRATION_NAME = "Swedish Calendar Plus"
CONFIG_VERSION: Final = 2
CONF_CALENDAR_NAME: Final = "calendar_name"
CONF_CATEGORIES: Final = "categories"
CONF_LANGUAGE: Final = "language"
CONF_INCLUDE_SUNDAYS: Final = "include_sundays"
CONF_RED_DAY_BRIDGE_DAYS: Final = "red_day_bridge_days"
CONF_INCLUDE_BRIDGE_DAYS: Final = "include_bridge_days"
CONF_OVERRIDE_SHARED_EVE_SETTINGS: Final = "override_shared_eve_settings"
SECTION_ADVANCED: Final = "advanced"

RED_DAY_EVE_KEYS: Final = (
    "epiphany_eve",
    "easter_eve",
    "walpurgis_night",
    "whitsun_eve",
    "midsummer_eve",
    "all_hallows_eve",
    "christmas_eve",
    "new_years_eve",
)
RED_DAY_EVE_OPTIONS: Final = tuple(f"red_day_{key}" for key in RED_DAY_EVE_KEYS)
CALENDAR_EVE_OPTIONS: Final = tuple(f"include_{key}" for key in RED_DAY_EVE_KEYS)

CATEGORY_HOLIDAYS: Final = "holidays"
CATEGORY_HOLIDAY_EVES: Final = "holiday_eves"
CATEGORY_NAME_DAYS: Final = "name_days"
CATEGORY_THEME_DAYS: Final = "theme_days"
CATEGORY_FLAG_DAYS: Final = "flag_days"
CALENDAR_CATEGORIES: Final = (
    CATEGORY_HOLIDAYS,
    CATEGORY_HOLIDAY_EVES,
    CATEGORY_NAME_DAYS,
    CATEGORY_THEME_DAYS,
    CATEGORY_FLAG_DAYS,
)
SUBENTRY_TYPE_CALENDAR: Final = "calendar"

DEFAULT_CALENDAR_NAME: Final = "Swedish holidays"
DEFAULT_LANGUAGE: Final = "sv"
DEFAULT_INCLUDE_SUNDAYS: Final = True
DEFAULT_CATEGORIES: Final = (CATEGORY_HOLIDAYS,)

LANGUAGE_ENGLISH: Final = "en"
LANGUAGE_SWEDISH: Final = "sv"
SUPPORTED_LANGUAGES: Final = (LANGUAGE_SWEDISH, LANGUAGE_ENGLISH)
