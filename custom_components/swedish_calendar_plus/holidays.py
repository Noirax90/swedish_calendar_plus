"""Calculate legal Swedish public holidays."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Final, Literal

from .localization import translate

Language = Literal["en", "sv"]
RedDayType = Literal["public_holiday", "sunday", "holiday_eve", "bridge_day"]
SUNDAY: Final = 6
SATURDAY: Final = 5


@dataclass(frozen=True, slots=True)
class SwedishHoliday:
    """A named legal Swedish public holiday."""

    key: str
    date: date

    def localized_name(self, language: Language) -> str:
        """Return the holiday name in the requested language."""
        return translate(language, f"events.{self.key}")


@dataclass(frozen=True, slots=True)
class SwedishHolidayEve:
    """An established Swedish holiday eve that is not a legal public holiday."""

    key: str
    date: date

    def localized_name(self, language: Language) -> str:
        """Return the holiday-eve name in the requested language."""
        return translate(language, f"events.{self.key}")


@dataclass(frozen=True, slots=True)
class _FixedHoliday:
    key: str
    month: int
    day: int


@dataclass(frozen=True, slots=True)
class DayPolicy:
    """User-configurable rules for which dates count as red."""

    include_sundays: bool = False
    red_day_eves: frozenset[str] = frozenset()
    include_bridge_days: bool = False


@dataclass(frozen=True, slots=True)
class DayClassification:
    """All supported classifications for one local calendar date."""

    day: date
    is_public_holiday: bool
    is_holiday_eve: bool
    is_bridge_day: bool
    is_red_day: bool
    is_workday: bool
    public_holiday: SwedishHoliday | None
    holiday_eve: SwedishHolidayEve | None
    red_day_key: str | None
    red_day_type: RedDayType | None


DEFAULT_DAY_POLICY: Final = DayPolicy()


FIXED_HOLIDAYS: Final = (
    _FixedHoliday("new_years_day", 1, 1),
    _FixedHoliday("epiphany", 1, 6),
    _FixedHoliday("may_day", 5, 1),
    _FixedHoliday("national_day", 6, 6),
    _FixedHoliday("christmas_day", 12, 25),
    _FixedHoliday("boxing_day", 12, 26),
)


def easter_sunday(year: int) -> date:
    """Return Gregorian Easter Sunday using the Meeus/Jones/Butcher algorithm."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    ell = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * ell) // 451
    month = (h + ell - 7 * m + 114) // 31
    day = (h + ell - 7 * m + 114) % 31 + 1
    return date(year, month, day)


def _first_weekday_in_range(
    start: date,
    end: date,
    weekday: int,
) -> date:
    """Return the first requested weekday in an inclusive date range."""
    result = start + timedelta(days=(weekday - start.weekday()) % 7)
    if result > end:
        msg = f"No weekday {weekday} occurs between {start} and {end}"
        raise ValueError(msg)
    return result


def named_holidays_for_year(year: int) -> tuple[SwedishHoliday, ...]:
    """Return all named legal Swedish holidays for a Gregorian year."""
    holidays = [
        SwedishHoliday(item.key, date(year, item.month, item.day))
        for item in FIXED_HOLIDAYS
    ]

    easter = easter_sunday(year)
    holidays.extend(
        (
            SwedishHoliday("good_friday", easter - timedelta(days=2)),
            SwedishHoliday("easter_sunday", easter),
            SwedishHoliday("easter_monday", easter + timedelta(days=1)),
            SwedishHoliday("ascension_day", easter + timedelta(days=39)),
            SwedishHoliday("whit_sunday", easter + timedelta(days=49)),
            SwedishHoliday(
                "midsummer_day",
                _first_weekday_in_range(
                    date(year, 6, 20),
                    date(year, 6, 26),
                    weekday=5,
                ),
            ),
            SwedishHoliday(
                "all_saints_day",
                _first_weekday_in_range(
                    date(year, 10, 31),
                    date(year, 11, 6),
                    weekday=5,
                ),
            ),
        )
    )
    return tuple(sorted(holidays, key=lambda holiday: (holiday.date, holiday.key)))


def holiday_eves_for_year(year: int) -> tuple[SwedishHolidayEve, ...]:
    """Return established Swedish holiday eves for a Gregorian year."""
    easter = easter_sunday(year)
    midsummer_day = _first_weekday_in_range(
        date(year, 6, 20),
        date(year, 6, 26),
        weekday=5,
    )
    all_saints_day = _first_weekday_in_range(
        date(year, 10, 31),
        date(year, 11, 6),
        weekday=5,
    )
    eves = (
        SwedishHolidayEve("epiphany_eve", date(year, 1, 5)),
        SwedishHolidayEve("easter_eve", easter - timedelta(days=1)),
        SwedishHolidayEve("walpurgis_night", date(year, 4, 30)),
        SwedishHolidayEve("whitsun_eve", easter + timedelta(days=48)),
        SwedishHolidayEve("midsummer_eve", midsummer_day - timedelta(days=1)),
        SwedishHolidayEve("all_hallows_eve", all_saints_day - timedelta(days=1)),
        SwedishHolidayEve("christmas_eve", date(year, 12, 24)),
        SwedishHolidayEve("new_years_eve", date(year, 12, 31)),
    )
    return tuple(sorted(eves, key=lambda item: item.date))


def holiday_eve_on(day: date) -> SwedishHolidayEve | None:
    """Return the holiday eve on a date, if present."""
    return next(
        (item for item in holiday_eves_for_year(day.year) if item.date == day),
        None,
    )


def named_holiday_on(day: date) -> SwedishHoliday | None:
    """Return a named holiday on a date, if present."""
    return next(
        (
            holiday
            for holiday in named_holidays_for_year(day.year)
            if holiday.date == day
        ),
        None,
    )


def is_bridge_day(
    day: date,
    *,
    red_day_eves: frozenset[str] = frozenset(),
) -> bool:
    """Return whether a weekday lies between two days off."""

    def _is_day_off(candidate: date) -> bool:
        eve = holiday_eve_on(candidate)
        return (
            candidate.weekday() in (SATURDAY, SUNDAY)
            or named_holiday_on(candidate) is not None
            or (eve is not None and eve.key in red_day_eves)
        )

    return (
        not _is_day_off(day)
        and _is_day_off(day - timedelta(days=1))
        and _is_day_off(day + timedelta(days=1))
    )


def red_day_type(key: str) -> RedDayType:
    """Return the machine-readable red-day type for an event key."""
    if key == "sunday":
        return "sunday"
    if key == "bridge_day":
        return "bridge_day"
    if key in {item.key for item in holiday_eves_for_year(2000)}:
        return "holiday_eve"
    return "public_holiday"


def classify_day(
    day: date, policy: DayPolicy = DEFAULT_DAY_POLICY
) -> DayClassification:
    """Return every supported classification for a date under one policy."""
    public_holiday = named_holiday_on(day)
    holiday_eve = holiday_eve_on(day)
    bridge_day = is_bridge_day(day, red_day_eves=policy.red_day_eves)

    red_key: str | None = None
    red_type: RedDayType | None = None
    if public_holiday is not None:
        red_key = public_holiday.key
        red_type = "public_holiday"
    elif holiday_eve is not None and holiday_eve.key in policy.red_day_eves:
        red_key = holiday_eve.key
        red_type = "holiday_eve"
    elif bridge_day and policy.include_bridge_days:
        red_key = "bridge_day"
        red_type = "bridge_day"
    elif day.weekday() == SUNDAY and policy.include_sundays:
        red_key = "sunday"
        red_type = "sunday"

    red_day = red_key is not None
    return DayClassification(
        day=day,
        is_public_holiday=public_holiday is not None,
        is_holiday_eve=holiday_eve is not None,
        is_bridge_day=bridge_day,
        is_red_day=red_day,
        is_workday=day.weekday() < SATURDAY and not red_day,
        public_holiday=public_holiday,
        holiday_eve=holiday_eve,
        red_day_key=red_key,
        red_day_type=red_type,
    )


def is_red_day(
    day: date,
    *,
    include_sundays: bool,
    red_day_eves: frozenset[str] = frozenset(),
    include_bridge_days: bool = False,
) -> bool:
    """Return whether a date counts as red under the configured policy."""
    return classify_day(
        day,
        DayPolicy(
            include_sundays=include_sundays,
            red_day_eves=red_day_eves,
            include_bridge_days=include_bridge_days,
        ),
    ).is_red_day


def holidays_between(
    start: date,
    end: date,
    *,
    include_sundays: bool,
    red_day_eves: frozenset[str] = frozenset(),
    include_bridge_days: bool = False,
) -> tuple[SwedishHoliday, ...]:
    """Return holidays in the half-open range [start, end)."""
    if end <= start:
        return ()

    holidays: dict[date, SwedishHoliday] = {}
    for year in range(start.year, end.year + 1):
        for holiday in named_holidays_for_year(year):
            if start <= holiday.date < end:
                holidays[holiday.date] = holiday
        for eve in holiday_eves_for_year(year):
            if eve.key in red_day_eves and start <= eve.date < end:
                holidays[eve.date] = SwedishHoliday(eve.key, eve.date)

    if include_sundays:
        current = start + timedelta(days=(SUNDAY - start.weekday()) % 7)
        while current < end:
            holidays.setdefault(
                current,
                SwedishHoliday("sunday", current),
            )
            current += timedelta(days=7)

    if include_bridge_days:
        current = start
        while current < end:
            if is_bridge_day(current, red_day_eves=red_day_eves):
                holidays.setdefault(
                    current,
                    SwedishHoliday("bridge_day", current),
                )
            current += timedelta(days=1)

    return tuple(sorted(holidays.values(), key=lambda holiday: holiday.date))
