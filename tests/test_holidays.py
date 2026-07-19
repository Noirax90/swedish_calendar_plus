"""Tests for legal Swedish holiday calculations."""

from datetime import date

from custom_components.swedish_calendar_plus.holidays import (
    DayPolicy,
    classify_day,
    easter_sunday,
    holiday_eves_for_year,
    holidays_between,
    is_bridge_day,
    is_red_day,
    named_holiday_on,
    named_holidays_for_year,
)


def test_easter_extremes() -> None:
    """Easter calculation handles known early and late dates."""
    assert easter_sunday(2008) == date(2008, 3, 23)
    assert easter_sunday(2038) == date(2038, 4, 25)


def test_all_named_holidays_for_2024() -> None:
    """The complete 2024 named holiday set matches known dates."""
    actual = {holiday.key: holiday.date for holiday in named_holidays_for_year(2024)}
    assert actual == {
        "new_years_day": date(2024, 1, 1),
        "epiphany": date(2024, 1, 6),
        "good_friday": date(2024, 3, 29),
        "easter_sunday": date(2024, 3, 31),
        "easter_monday": date(2024, 4, 1),
        "may_day": date(2024, 5, 1),
        "ascension_day": date(2024, 5, 9),
        "whit_sunday": date(2024, 5, 19),
        "national_day": date(2024, 6, 6),
        "midsummer_day": date(2024, 6, 22),
        "all_saints_day": date(2024, 11, 2),
        "christmas_day": date(2024, 12, 25),
        "boxing_day": date(2024, 12, 26),
    }


def test_sunday_policy() -> None:
    """Ordinary Sundays follow the option; named Sundays always remain red."""
    ordinary_sunday = date(2024, 2, 4)
    easter = date(2024, 3, 31)

    assert is_red_day(ordinary_sunday, include_sundays=True)
    assert not is_red_day(ordinary_sunday, include_sundays=False)
    assert is_red_day(easter, include_sundays=False)


def test_range_adds_sundays_without_duplicating_named_holidays() -> None:
    """A named Sunday takes precedence over the generic Sunday event."""
    holidays = holidays_between(
        date(2024, 3, 29),
        date(2024, 4, 2),
        include_sundays=True,
    )
    assert [holiday.key for holiday in holidays] == [
        "good_friday",
        "easter_sunday",
        "easter_monday",
    ]


def test_half_open_range_and_year_boundary() -> None:
    """Range end is exclusive and calculations cross years."""
    holidays = holidays_between(
        date(2024, 12, 26),
        date(2025, 1, 2),
        include_sundays=False,
    )
    assert [(holiday.key, holiday.date) for holiday in holidays] == [
        ("boxing_day", date(2024, 12, 26)),
        ("new_years_day", date(2025, 1, 1)),
    ]


def test_localized_names() -> None:
    """Named holidays expose Swedish and English names."""
    holiday = named_holiday_on(date(2024, 6, 6))
    assert holiday is not None
    assert holiday.localized_name("sv") == "Sveriges nationaldag"
    assert holiday.localized_name("en") == "National Day of Sweden"


def test_established_holiday_eves_for_2026() -> None:
    """Holiday eves include all established dates and are not red days."""
    eves = {item.key: item for item in holiday_eves_for_year(2026)}

    assert {key: item.date for key, item in eves.items()} == {
        "epiphany_eve": date(2026, 1, 5),
        "easter_eve": date(2026, 4, 4),
        "walpurgis_night": date(2026, 4, 30),
        "whitsun_eve": date(2026, 5, 23),
        "midsummer_eve": date(2026, 6, 19),
        "all_hallows_eve": date(2026, 10, 30),
        "christmas_eve": date(2026, 12, 24),
        "new_years_eve": date(2026, 12, 31),
    }
    assert eves["christmas_eve"].localized_name("sv") == "Julafton"
    assert eves["christmas_eve"].localized_name("en") == "Christmas Eve"
    assert not is_red_day(date(2026, 12, 24), include_sundays=True)


def test_configured_holiday_eve_counts_as_red_day_and_calendar_holiday() -> None:
    """An individually selected holiday eve follows the red-day policy."""
    christmas_eve = date(2026, 12, 24)
    configured_eves = frozenset({"christmas_eve"})

    assert is_red_day(
        christmas_eve,
        include_sundays=False,
        red_day_eves=configured_eves,
    )
    assert [
        holiday.key
        for holiday in holidays_between(
            christmas_eve,
            date(2026, 12, 25),
            include_sundays=False,
            red_day_eves=configured_eves,
        )
    ] == ["christmas_eve"]


def test_weekday_between_holiday_and_weekend_is_bridge_day() -> None:
    """The Friday after Ascension is a bridge day but only optionally red."""
    bridge_day = date(2026, 5, 15)

    assert is_bridge_day(bridge_day)
    assert not is_red_day(bridge_day, include_sundays=True)
    assert is_red_day(
        bridge_day,
        include_sundays=True,
        include_bridge_days=True,
    )


def test_day_classification_keeps_fact_and_policy_separate() -> None:
    """Classification exposes bridge-day facts independently of red-day policy."""
    bridge_day = date(2026, 5, 15)

    standard = classify_day(bridge_day)
    configured = classify_day(
        bridge_day,
        DayPolicy(include_bridge_days=True),
    )

    assert standard.is_bridge_day
    assert not standard.is_red_day
    assert standard.is_workday
    assert configured.is_bridge_day
    assert configured.is_red_day
    assert not configured.is_workday
    assert configured.red_day_type == "bridge_day"
    assert configured.red_day_key == "bridge_day"


def test_day_classification_prioritizes_named_holiday() -> None:
    """A legal holiday supplies the primary red-day reason."""
    classification = classify_day(
        date(2024, 3, 31),
        DayPolicy(include_sundays=True),
    )

    assert classification.is_public_holiday
    assert classification.is_red_day
    assert not classification.is_workday
    assert classification.public_holiday is not None
    assert classification.red_day_type == "public_holiday"
    assert classification.red_day_key == "easter_sunday"
