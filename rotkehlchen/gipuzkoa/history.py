from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from rotkehlchen.accounting.constants import DEFAULT, EVENT_CATEGORY_MAPPINGS, EXCHANGE
from rotkehlchen.exchanges.constants import ALL_SUPPORTED_EXCHANGES
from rotkehlchen.history.events.structures.types import EventCategoryGroup, EventDirection
from rotkehlchen.utils.misc import ts_ms_to_sec

if TYPE_CHECKING:
    from rotkehlchen.history.events.structures.base import HistoryBaseEntry


GIPUZKOA_TIMEZONE = ZoneInfo('Europe/Madrid')
GIPUZKOA_FISCAL_RULESET = 'gipuzkoa-v1'


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


def _get_gipuzkoa_fiscal_classification(technical_classification: str) -> str:
    """Return CryptoLedger's preliminary Gipuzkoa fiscal classification.

    A technical disposal is a candidate for capital gain or loss treatment.
    A technical income event requires further review because its final IRPF
    category depends on facts that are not represented by the technical label.
    Staking and validator rewards also require review because the technical
    category alone does not determine their final IRPF treatment.
    A technical transfer requires an ownership check because moving an asset
    between accounts does not by itself establish a change in beneficial ownership.
    A technical expense requires a deductibility review because its tax treatment
    depends on the nature, purpose, and factual connection of the expense.
    A technical loss requires tax review because some losses are not computable
    for IRPF and the technical label does not establish their tax treatment.
    """
    if technical_classification == 'disposal':
        return 'capital_gain_or_loss_candidate'

    if technical_classification == 'income':
        return 'income_requires_review'

    if technical_classification in {'staking', 'validator'}:
        return 'staking_requires_review'

    if technical_classification == 'transfer':
        return 'transfer_requires_ownership_check'

    if technical_classification == 'expense':
        return 'expense_requires_deductibility_review'

    if technical_classification == 'loss':
        return 'loss_requires_tax_review'

    return 'unknown'


def get_gipuzkoa_history_metadata(event: HistoryBaseEntry) -> dict[str, int | str]:
    """Return Gipuzkoa-specific metadata exposed by the history events API."""
    technical_classification = _get_gipuzkoa_classification(event)

    return {
        'tax_year': datetime.fromtimestamp(
            ts_ms_to_sec(event.timestamp),
            tz=GIPUZKOA_TIMEZONE,
        ).year,
        'classification': technical_classification,
        'technical_classification': technical_classification,
        'fiscal_classification': _get_gipuzkoa_fiscal_classification(
            technical_classification,
        ),
        'fiscal_ruleset': GIPUZKOA_FISCAL_RULESET,
    }
