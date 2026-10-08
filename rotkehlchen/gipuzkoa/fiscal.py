from __future__ import annotations

from typing import TYPE_CHECKING

from rotkehlchen.accounting.constants import DEFAULT, EVENT_CATEGORY_MAPPINGS, EXCHANGE
from rotkehlchen.exchanges.constants import ALL_SUPPORTED_EXCHANGES
from rotkehlchen.history.events.structures.types import (
    EventCategoryGroup,
    HistoryEventType,
)

if TYPE_CHECKING:
    from rotkehlchen.history.events.structures.base import HistoryBaseEntry


GIPUZKOA_FISCAL_RULESET = 'gipuzkoa-v1'


def _get_gipuzkoa_event_category_group(
        event: HistoryBaseEntry,
) -> EventCategoryGroup | None:
    """Return rotki's resolved category group for a history event."""
    event_type_mapping = EVENT_CATEGORY_MAPPINGS.get(event.event_type)
    if event_type_mapping is None:
        return None

    category_mapping = event_type_mapping.get(event.event_subtype)
    if category_mapping is None:
        return None

    if (
        EXCHANGE in category_mapping and
        event.location in ALL_SUPPORTED_EXCHANGES
    ):
        category = category_mapping.get(EXCHANGE)
    else:
        category = category_mapping.get(DEFAULT)

    if category is None:
        return None

    return category.group


def get_gipuzkoa_fiscal_classification(
        technical_classification: str,
        event: HistoryBaseEntry | None = None,
) -> str:
    """Return CryptoLedger's preliminary Gipuzkoa fiscal classification.

    The optional history event is available for rules that need more context than
    the technical classification alone.

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
    A technical donation requires tax review because gratuitous transfers can
    involve both IRPF consequences and succession/donation tax considerations.
    A technical DeFi event requires protocol-level review because deposits,
    withdrawals, borrowing, and repayment can have different tax consequences.
    DeFi deposit/withdraw events and borrow/repay events are therefore kept as
    separate review categories when the event context identifies their group.
    A technical NFT event requires transaction-level review because minting,
    acquiring, selling, and transferring an NFT can have different tax consequences.
    An NFT mint is kept as a separate review category because minting alone does
    not establish whether value was received, created, or transferred.
    A technical acquisition requires source review because purchases, swaps,
    gratuitous acquisitions, and other sources can have different tax consequences.
    An acquisition recorded at a supported exchange requires trade-pair review
    because the paired leg determines whether the acquisition was made against
    fiat or another cryptoasset.
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

    if technical_classification == 'donation':
        return 'donation_requires_tax_review'

    if technical_classification == 'defi':
        if event is not None:
            category_group = _get_gipuzkoa_event_category_group(event)
            if category_group == EventCategoryGroup.DEFI_DEPOSIT_WITHDRAW:
                return 'defi_deposit_withdraw_requires_protocol_review'
            if category_group == EventCategoryGroup.DEFI_BORROW_REPAY:
                return 'defi_borrow_repay_requires_protocol_review'

        return 'defi_requires_protocol_review'

    if technical_classification == 'nft':
        if event is not None and event.event_type == HistoryEventType.MINT:
            return 'nft_mint_requires_origin_review'

        return 'nft_requires_transaction_review'

    if technical_classification == 'acquisition':
        if event is not None and event.location in ALL_SUPPORTED_EXCHANGES:
            return 'acquisition_exchange_requires_trade_pair_review'

        return 'acquisition_requires_source_review'

    return 'unknown'
