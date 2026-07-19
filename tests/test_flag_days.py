"""Tests for official Swedish flag-day calculations."""

from datetime import date

from custom_components.swedish_calendar_plus.flag_days import flag_days_for_year


def test_flag_days_for_parliamentary_election_year() -> None:
    """The complete official 2026 list includes calculated election day."""
    actual = {item.key: item.date for item in flag_days_for_year(2026)}

    assert actual == {
        "flag_new_years_day": date(2026, 1, 1),
        "flag_kings_name_day": date(2026, 1, 28),
        "flag_crown_princess_name_day": date(2026, 3, 12),
        "flag_easter_sunday": date(2026, 4, 5),
        "flag_kings_birthday": date(2026, 4, 30),
        "flag_may_day": date(2026, 5, 1),
        "flag_whit_sunday": date(2026, 5, 24),
        "flag_veterans_day": date(2026, 5, 29),
        "flag_national_day": date(2026, 6, 6),
        "flag_midsummer_day": date(2026, 6, 20),
        "flag_crown_princess_birthday": date(2026, 7, 14),
        "flag_queens_name_day": date(2026, 8, 8),
        "flag_parliamentary_election_day": date(2026, 9, 13),
        "flag_un_day": date(2026, 10, 24),
        "flag_gustav_adolf_day": date(2026, 11, 6),
        "flag_nobel_day": date(2026, 12, 10),
        "flag_queens_birthday": date(2026, 12, 23),
        "flag_christmas_day": date(2026, 12, 25),
    }


def test_eu_election_day_uses_published_date_only() -> None:
    """EU election dates are explicit because no annual date rule exists."""
    actual = {item.key: item.date for item in flag_days_for_year(2024)}

    assert actual["flag_eu_election_day"] == date(2024, 6, 9)
    assert "flag_parliamentary_election_day" not in actual
    assert "flag_eu_election_day" not in {item.key for item in flag_days_for_year(2025)}
