"""Calculate Sweden's official flag days."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Final

from .holidays import Language, easter_sunday, named_holiday_on
from .localization import translate


@dataclass(frozen=True, slots=True)
class SwedishFlagDay:
    """An official Swedish flag day."""

    key: str
    date: date

    def localized_name(self, language: Language) -> str:
        """Return the flag-day name in the requested language."""
        return translate(language, f"event_{self.key}")


FIXED_FLAG_DAYS: Final = (
    ("flag_new_years_day", 1, 1),
    ("flag_kings_name_day", 1, 28),
    ("flag_crown_princess_name_day", 3, 12),
    ("flag_kings_birthday", 4, 30),
    ("flag_may_day", 5, 1),
    ("flag_veterans_day", 5, 29),
    ("flag_national_day", 6, 6),
    ("flag_crown_princess_birthday", 7, 14),
    ("flag_queens_name_day", 8, 8),
    ("flag_un_day", 10, 24),
    ("flag_gustav_adolf_day", 11, 6),
    ("flag_nobel_day", 12, 10),
    ("flag_queens_birthday", 12, 23),
    ("flag_christmas_day", 12, 25),
)

# An EU election has no permanent calendar rule. Add its officially decided
# Swedish date here once published instead of projecting an assumed date.
EU_ELECTION_DATES: Final = {
    2009: date(2009, 6, 7),
    2014: date(2014, 5, 25),
    2019: date(2019, 5, 26),
    2024: date(2024, 6, 9),
}
FIRST_FOUR_YEAR_PARLIAMENTARY_ELECTION: Final = 1994
PARLIAMENTARY_ELECTION_BASE_YEAR: Final = 2022


def _second_sunday_in_september(year: int) -> date:
    """Return the ordinary Swedish parliamentary election day."""
    first = date(year, 9, 1)
    first_sunday = first + timedelta(days=(6 - first.weekday()) % 7)
    return first_sunday + timedelta(days=7)


def flag_days_for_year(year: int) -> tuple[SwedishFlagDay, ...]:
    """Return official Swedish flag days for a calendar year."""
    result = [
        SwedishFlagDay(key, date(year, month, day))
        for key, month, day in FIXED_FLAG_DAYS
    ]
    easter = easter_sunday(year)
    result.extend(
        (
            SwedishFlagDay("flag_easter_sunday", easter),
            SwedishFlagDay("flag_whit_sunday", easter + timedelta(days=49)),
        )
    )
    midsummer = next(
        candidate
        for day in range(20, 27)
        if (candidate := named_holiday_on(date(year, 6, day))) is not None
        and candidate.key == "midsummer_day"
    )
    result.append(SwedishFlagDay("flag_midsummer_day", midsummer.date))

    if (
        year >= FIRST_FOUR_YEAR_PARLIAMENTARY_ELECTION
        and (year - PARLIAMENTARY_ELECTION_BASE_YEAR) % 4 == 0
    ):
        result.append(
            SwedishFlagDay(
                "flag_parliamentary_election_day",
                _second_sunday_in_september(year),
            )
        )
    if election_day := EU_ELECTION_DATES.get(year):
        result.append(SwedishFlagDay("flag_eu_election_day", election_day))

    return tuple(sorted(result, key=lambda item: (item.date, item.key)))
