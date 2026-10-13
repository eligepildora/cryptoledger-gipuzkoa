from types import SimpleNamespace

import pytest

from rotkehlchen.constants.assets import A_ETH
from rotkehlchen.fval import FVal
from rotkehlchen.gipuzkoa.report import get_gipuzkoa_report_income_reviews
from rotkehlchen.history.events.structures.base import HistoryEvent
from rotkehlchen.history.events.structures.types import (
    HistoryEventSubType,
    HistoryEventType,
)
from rotkehlchen.types import Location, TimestampMS


@pytest.mark.parametrize(
    ('identifier', 'event_type', 'event_subtype', 'expected_technical'),
    [
        (
            101,
            HistoryEventType.RECEIVE,
            HistoryEventSubType.REWARD,
            'income',
        ),
        (
            102,
            HistoryEventType.STAKING,
            HistoryEventSubType.DEPOSIT_ASSET,
            'staking',
        ),
        (
            103,
            HistoryEventType.INFORMATIONAL,
            HistoryEventSubType.BLOCK_PRODUCTION,
            'validator',
        ),
    ],
)
def test_get_gipuzkoa_report_income_reviews(
        monkeypatch: pytest.MonkeyPatch,
        identifier: int,
        event_type: HistoryEventType,
        event_subtype: HistoryEventSubType,
        expected_technical: str,
) -> None:
    history_event = HistoryEvent(
        identifier=identifier,
        group_identifier=f'gipuzkoa-report-income-{identifier}',
        sequence_index=0,
        timestamp=TimestampMS(1748736000000),
        location=Location.EXTERNAL,
        event_type=event_type,
        event_subtype=event_subtype,
        asset=A_ETH,
        amount=FVal('1'),
        notes='Gipuzkoa income review',
    )
    processed_event = SimpleNamespace(
        extra_data={'originating_event_id': identifier},
    )

    monkeypatch.setattr(
        'rotkehlchen.gipuzkoa.report._load_gipuzkoa_report_context',
        lambda dbreport, report_id: (
            [processed_event],
            {identifier: history_event},
        ),
    )

    result = get_gipuzkoa_report_income_reviews(
        dbreport=object(),
        report_id=42,
    )

    assert len(result) == 1
    assert result[0]['originating_event_id'] == identifier
    assert result[0]['tax_year'] == 2025
    assert result[0]['technical_classification'] == expected_technical
    assert result[0]['fiscal_classification'] != 'unknown'
