from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class WfoWindow:
    round_id: int
    train_start: date
    train_end: date
    gap_start: date
    gap_end: date
    test_start: date
    test_end: date


def _add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return date(year, month, day)


def _period_end(start: date, months: int) -> date:
    return _add_months(start, months) - timedelta(days=1)


def _validate_positive_months(**months: int) -> None:
    for name, value in months.items():
        if value <= 0:
            raise ValueError(f"{name} must be > 0")


def generate_wfo_windows(
    start_date: date,
    end_date: date,
    train_months: int = 36,
    gap_months: int = 1,
    test_months: int = 6,
    step_months: int = 6,
) -> list[WfoWindow]:
    if start_date >= end_date:
        raise ValueError("start_date must be before end_date")

    _validate_positive_months(
        train_months=train_months,
        gap_months=gap_months,
        test_months=test_months,
        step_months=step_months,
    )

    windows: list[WfoWindow] = []
    round_id = 1
    train_start = start_date

    while True:
        train_end = _period_end(train_start, train_months)
        gap_start = train_end + timedelta(days=1)
        gap_end = _period_end(gap_start, gap_months)
        test_start = gap_end + timedelta(days=1)
        test_end = _period_end(test_start, test_months)

        if test_end > end_date:
            break

        windows.append(
            WfoWindow(
                round_id=round_id,
                train_start=train_start,
                train_end=train_end,
                gap_start=gap_start,
                gap_end=gap_end,
                test_start=test_start,
                test_end=test_end,
            )
        )

        round_id += 1
        train_start = _add_months(train_start, step_months)

    return windows
