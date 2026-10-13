from types import SimpleNamespace

import pytest

from rotkehlchen.constants.assets import A_ETH
from rotkehlchen.fval import FVal
from rotkehlchen.gipuzkoa.report import get_gipuzkoa_report_defi_reviews
from rotkehlchen.history.events.structures.base import HistoryEvent
from rotkehlchen.history.events.structures.types import (
    HistoryEventSubType,
    HistoryEventType,
)
from rotkehlchen.types import Location, TimestampMS


def test_get_gipuzkoa_report_defi_reviews(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    history_event = HistoryEvent(
        identifier=123,
        group_identifier='gipuzkoa-report-defi',
        sequence_index=0,
        timestamp=TimestampMS(1748736000000),
        location=Location.EXTERNAL,
        event_type=HistoryEventType.DEPOSIT,
        event_subtype=HistoryEventSubType.DEPOSIT_TO_PROTOCOL,
        asset=A_ETH,
        amount=FVal('1'),
        notes='Gipuzkoa DeFi deposit',
    )
    processed_event = SimpleNamespace(
        extra_data={'originating_event_id': 123},
    )

    monkeypatch.setattr(
        'rotkehlchen.gipuzkoa.report._load_gipuzkoa_report_context',
        lambda dbreport, report_id: (
            [processed_event],
            {123: history_event},
        ),
    )

    result = get_gipuzkoa_report_defi_reviews(
        dbreport=object(),
        report_id=42,
    )

    assert result == [{
        'originating_event_id': 123,
        'tax_year': 2025,
        'fiscal_classification': (
            'defi_deposit_withdraw_requires_protocol_review'
        ),
    }]
