from rotkehlchen.accounting.mixins.event import AccountingEventType
from rotkehlchen.accounting.structures.balance import Balance
from rotkehlchen.accounting.structures.processed_event import ProcessedAccountingEvent
from rotkehlchen.constants import ZERO
from rotkehlchen.constants.assets import A_ETH
from rotkehlchen.fval import FVal
from rotkehlchen.gipuzkoa.nft import collect_gipuzkoa_nft_reviews
from rotkehlchen.history.events.structures.base import HistoryEvent
from rotkehlchen.history.events.structures.types import (
    HistoryEventSubType,
    HistoryEventType,
)
from rotkehlchen.types import Location, Price, Timestamp, TimestampMS


def test_collect_gipuzkoa_nft_reviews() -> None:
    history_event = HistoryEvent(
        identifier=123,
        group_identifier='gipuzkoa-nft-review',
        sequence_index=0,
        timestamp=TimestampMS(1748736000000),
        location=Location.EXTERNAL,
        event_type=HistoryEventType.MINT,
        event_subtype=HistoryEventSubType.NFT,
        asset=A_ETH,
        amount=FVal('1'),
        notes='Gipuzkoa NFT mint',
    )

    processed_event = ProcessedAccountingEvent(
        event_type=AccountingEventType.TRANSACTION_EVENT,
        notes='Processed Gipuzkoa NFT event',
        location=Location.EXTERNAL,
        timestamp=Timestamp(1748736000),
        asset=A_ETH,
        free_amount=ZERO,
        taxable_amount=FVal('1'),
        price=Price(FVal('2000')),
        pnl=Balance(),
        cost_basis=None,
        index=0,
        extra_data={
            'direction': 'out',
            'originating_event_id': 123,
        },
    )

    reviews = collect_gipuzkoa_nft_reviews(
        events=[processed_event],
        history_events_by_id={123: history_event},
    )

    assert len(reviews) == 1
    assert reviews[0].originating_event_id == 123
    assert reviews[0].tax_year == 2025
    assert reviews[0].fiscal_classification == (
        'nft_mint_requires_origin_review'
    )


def test_collect_gipuzkoa_nft_reviews_ignores_non_nft() -> None:
    history_event = HistoryEvent(
        identifier=456,
        group_identifier='gipuzkoa-transfer-review',
        sequence_index=0,
        timestamp=TimestampMS(1748736000000),
        location=Location.EXTERNAL,
        event_type=HistoryEventType.TRANSFER,
        event_subtype=HistoryEventSubType.NONE,
        asset=A_ETH,
        amount=FVal('1'),
        notes='Gipuzkoa transfer',
    )

    processed_event = ProcessedAccountingEvent(
        event_type=AccountingEventType.TRANSACTION_EVENT,
        notes='Processed Gipuzkoa transfer',
        location=Location.EXTERNAL,
        timestamp=Timestamp(1748736000),
        asset=A_ETH,
        free_amount=ZERO,
        taxable_amount=FVal('1'),
        price=Price(FVal('2000')),
        pnl=Balance(),
        cost_basis=None,
        index=0,
        extra_data={
            'direction': 'out',
            'originating_event_id': 456,
        },
    )

    reviews = collect_gipuzkoa_nft_reviews(
        events=[processed_event],
        history_events_by_id={456: history_event},
    )

    assert reviews == []
