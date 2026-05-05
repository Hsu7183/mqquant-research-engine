from datetime import date

import pytest

from mqre_v2.validation.wfo.windows import WfoWindow, generate_wfo_windows


def test_generate_wfo_windows_multiple_rounds() -> None:
    windows = generate_wfo_windows(date(2020, 1, 1), date(2024, 12, 31))

    assert len(windows) == 3
    assert all(isinstance(window, WfoWindow) for window in windows)


def test_first_wfo_window_dates_are_correct() -> None:
    first = generate_wfo_windows(date(2020, 1, 1), date(2024, 12, 31))[0]

    assert first == WfoWindow(
        round_id=1,
        train_start=date(2020, 1, 1),
        train_end=date(2022, 12, 31),
        gap_start=date(2023, 1, 1),
        gap_end=date(2023, 1, 31),
        test_start=date(2023, 2, 1),
        test_end=date(2023, 7, 31),
    )


def test_round_ids_increment_from_one() -> None:
    windows = generate_wfo_windows(date(2020, 1, 1), date(2024, 12, 31))

    assert [window.round_id for window in windows] == [1, 2, 3]


def test_does_not_generate_round_with_test_end_after_end_date() -> None:
    end_date = date(2024, 12, 31)
    windows = generate_wfo_windows(date(2020, 1, 1), end_date)

    assert windows
    assert all(window.test_end <= end_date for window in windows)
    assert windows[-1].test_end == date(2024, 7, 31)


@pytest.mark.parametrize(
    ("start_date", "end_date"),
    [
        (date(2024, 1, 1), date(2024, 1, 1)),
        (date(2024, 1, 2), date(2024, 1, 1)),
    ],
)
def test_start_date_must_be_before_end_date(start_date: date, end_date: date) -> None:
    with pytest.raises(ValueError, match="start_date must be before end_date"):
        generate_wfo_windows(start_date, end_date)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"train_months": 0},
        {"gap_months": 0},
        {"test_months": 0},
        {"step_months": 0},
    ],
)
def test_month_parameters_must_be_positive(kwargs: dict[str, int]) -> None:
    with pytest.raises(ValueError, match="must be > 0"):
        generate_wfo_windows(date(2020, 1, 1), date(2024, 12, 31), **kwargs)
