from rotkehlchen.gipuzkoa.dates import (
    get_gipuzkoa_tax_year,
    get_gipuzkoa_tax_year_ms,
)
from rotkehlchen.types import Timestamp, TimestampMS


def test_gipuzkoa_tax_year_seconds() -> None:
    assert get_gipuzkoa_tax_year(
        Timestamp(1735687800),
    ) == 2025


def test_gipuzkoa_tax_year_milliseconds() -> None:
    assert get_gipuzkoa_tax_year_ms(
        TimestampMS(1735687800000),
    ) == 2025
