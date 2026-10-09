from datetime import datetime
from zoneinfo import ZoneInfo

from rotkehlchen.types import Timestamp, TimestampMS
from rotkehlchen.utils.misc import ts_ms_to_sec


GIPUZKOA_TIMEZONE = ZoneInfo('Europe/Madrid')


def get_gipuzkoa_tax_year(timestamp: Timestamp) -> int:
    """Return the Gipuzkoa tax year for a timestamp expressed in seconds."""
    return datetime.fromtimestamp(
        timestamp,
        tz=GIPUZKOA_TIMEZONE,
    ).year


def get_gipuzkoa_tax_year_ms(timestamp: TimestampMS) -> int:
    """Return the Gipuzkoa tax year for a timestamp expressed in milliseconds."""
    return get_gipuzkoa_tax_year(
        Timestamp(ts_ms_to_sec(timestamp)),
    )
