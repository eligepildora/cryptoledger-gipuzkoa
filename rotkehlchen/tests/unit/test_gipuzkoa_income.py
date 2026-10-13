from types import SimpleNamespace

import pytest

from rotkehlchen.constants.assets import A_ETH
from rotkehlchen.fval import FVal
from rotkehlchen.gipuzkoa.income import collect_gipuzkoa_income_reviews
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
def test_collect_gipuzkoa_income_reviews(
        identifier: int,
        event_type: HistoryEventType,
        event_subtype: HistoryEventSubType,
        expected_technical: str,
) -> None:
    history_event = HistoryEvent(
        identifier=identifier,
        group_identifier=f'gipuzkoa-income-{identifier}',
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

    reviews = collect_gipuzkoa_income_reviews(
        events=[processed_event],
        history_events_by_id={identifier: history_event},
    )

    assert len(reviews) == 1
    assert reviews[0].originating_event_id == identifier
    assert reviews[0].tax_year == 2025
    assert reviews[0].technical_classification == expected_technical
    assert reviews[0].fiscal_classification != 'unknown'


def test_collect_gipuzkoa_income_reviews_ignores_transfer() -> None:
    history_event = HistoryEvent(
        identifier=456,
        group_identifier='gipuzkoa-income-transfer',
        sequence_index=0,
        timestamp=TimestampMS(1748736000000),
        location=Location.EXTERNAL,
        event_type=HistoryEventType.TRANSFER,
        event_subtype=HistoryEventSubType.NONE,
        asset=A_ETH,
        amount=FVal('1'),
        notes='Gipuzkoa transfer',
    )

    processed_event = SimpleNamespace(
        extra_data={'originating_event_id': 456},
    )

    assert collect_gipuzkoa_income_reviews(
        events=[processed_event],
        history_events_by_id={456: history_event},
    ) == []
