from __future__ import annotations

from typing import TYPE_CHECKING

from rotkehlchen.accounting.constants import DEFAULT, EVENT_CATEGORY_MAPPINGS, EXCHANGE
from rotkehlchen.exchanges.constants import ALL_SUPPORTED_EXCHANGES
from rotkehlchen.gipuzkoa.dates import get_gipuzkoa_tax_year_ms
from rotkehlchen.gipuzkoa.fiscal import (
    GIPUZKOA_FISCAL_RULESET,
    get_gipuzkoa_fiscal_classification,
)
from rotkehlchen.history.events.structures.types import EventCategoryGroup, EventDirection

if TYPE_CHECKING:
    from rotkehlchen.history.events.structures.base import HistoryBaseEntry


def _get_gipuzkoa_classification(event: HistoryBaseEntry) -> str:
    """Return CryptoLedger's technical classification for a history event."""
    event_type_mapping = EVENT_CATEGORY_MAPPINGS.get(event.event_type)
    if event_type_mapping is None:
        return 'unknown'

    category_mapping = event_type_mapping.get(event.event_subtype)
    if category_mapping is None:
        return 'unknown'

    if (
        EXCHANGE in category_mapping and
        event.location in ALL_SUPPORTED_EXCHANGES
    ):
        category = category_mapping.get(EXCHANGE)
    else:
        category = category_mapping.get(DEFAULT)

    if category is None:
        return 'unknown'

    if category.group == EventCategoryGroup.TRADE:
        if category.direction == EventDirection.OUT:
            return 'disposal'
        if category.direction == EventDirection.IN:
            return 'acquisition'
        return 'unknown'

    return {
        EventCategoryGroup.TRANSFER: 'transfer',
        EventCategoryGroup.CEX: 'transfer',
        EventCategoryGroup.BRIDGE: 'transfer',
        EventCategoryGroup.INCOME: 'income',
        EventCategoryGroup.EXPENSE: 'expense',
        EventCategoryGroup.LOSS: 'loss',
        EventCategoryGroup.STAKING: 'staking',
        EventCategoryGroup.DONATION: 'donation',
        EventCategoryGroup.DEFI_DEPOSIT_WITHDRAW: 'defi',
        EventCategoryGroup.DEFI_BORROW_REPAY: 'defi',
        EventCategoryGroup.VALIDATOR: 'validator',
        EventCategoryGroup.NFT: 'nft',
    }.get(category.group, 'unknown')


def get_gipuzkoa_history_metadata(event: HistoryBaseEntry) -> dict[str, int | str]:
    """Return Gipuzkoa-specific metadata exposed by the history events API."""
    technical_classification = _get_gipuzkoa_classification(event)

    return {
        'tax_year': get_gipuzkoa_tax_year_ms(event.timestamp),
        'classification': technical_classification,
        'technical_classification': technical_classification,
        'fiscal_classification': get_gipuzkoa_fiscal_classification(
            technical_classification,
            event=event,
        ),
        'fiscal_ruleset': GIPUZKOA_FISCAL_RULESET,
    }
