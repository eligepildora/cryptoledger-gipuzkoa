from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rotkehlchen.history.events.structures.base import HistoryBaseEntry


GIPUZKOA_FISCAL_RULESET = 'gipuzkoa-v1'


def get_gipuzkoa_fiscal_classification(
        technical_classification: str,
        event: HistoryBaseEntry | None = None,
) -> str:
    """Return CryptoLedger's preliminary Gipuzkoa fiscal classification.

    The optional history event is available for rules that need more context than
    the technical classification alone. Current rules intentionally preserve the
    existing behavior and do not yet depend on event-specific fields.

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
    A technical NFT event requires transaction-level review because minting,
    acquiring, selling, and transferring an NFT can have different tax consequences.
    A technical acquisition requires source review because purchases, swaps,
    gratuitous acquisitions, and other sources can have different tax consequences.
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
        return 'defi_requires_protocol_review'

    if technical_classification == 'nft':
        return 'nft_requires_transaction_review'

    if technical_classification == 'acquisition':
        return 'acquisition_requires_source_review'

    return 'unknown'
