from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from rotkehlchen.accounting.cost_basis import CostBasisInfo
from rotkehlchen.constants import ZERO
from rotkehlchen.fval import FVal

if TYPE_CHECKING:
    from rotkehlchen.accounting.structures.processed_event import ProcessedAccountingEvent


@dataclass(frozen=True)
class GipuzkoaDisposalCalculation:
    """Result of a preliminary Gipuzkoa disposal calculation in EUR."""

    disposal_value_eur: FVal
    acquisition_cost_eur: FVal
    disposal_expenses_eur: FVal
    net_disposal_value_eur: FVal
    gain_loss_eur: FVal


def get_gipuzkoa_acquisition_cost_eur(
        cost_basis: CostBasisInfo,
) -> FVal:
    """Return acquisition cost in EUR from rotki matched acquisitions.

    The matched acquisitions are used instead of the aggregate bought-cost fields
    because matched acquisition data survives cost-basis serialization.
    """
    if not cost_basis.is_complete:
        raise ValueError('Cannot calculate Gipuzkoa acquisition cost from incomplete cost basis')

    acquisition_cost_eur = ZERO
    for matched_acquisition in cost_basis.matched_acquisitions:
        acquisition_cost_eur += (
            matched_acquisition.amount *
            matched_acquisition.event.rate
        )

    return acquisition_cost_eur


def calculate_gipuzkoa_disposal(
        disposal_value_eur: FVal,
        acquisition_cost_eur: FVal,
        disposal_expenses_eur: FVal,
) -> GipuzkoaDisposalCalculation:
    """Calculate the preliminary gain or loss for a cryptoasset disposal.

    This function only performs the arithmetic once the EUR disposal value,
    acquisition cost, and disposal expenses have already been determined.
    Cost-basis lot selection and EUR price resolution belong to separate layers.
    """
    net_disposal_value_eur = disposal_value_eur - disposal_expenses_eur
    gain_loss_eur = net_disposal_value_eur - acquisition_cost_eur

    return GipuzkoaDisposalCalculation(
        disposal_value_eur=disposal_value_eur,
        acquisition_cost_eur=acquisition_cost_eur,
        disposal_expenses_eur=disposal_expenses_eur,
        net_disposal_value_eur=net_disposal_value_eur,
        gain_loss_eur=gain_loss_eur,
    )


def calculate_gipuzkoa_processed_disposal(
        event: ProcessedAccountingEvent,
        disposal_expenses_eur: FVal = ZERO,
) -> GipuzkoaDisposalCalculation:
    """Calculate a Gipuzkoa disposal from a rotki processed accounting event.

    The full disposed amount is used instead of rotki's taxable/free split because
    Gipuzkoa fiscal treatment must be determined independently from other
    jurisdiction-specific accounting settings.
    """
    if event.cost_basis is None:
        raise ValueError('Cannot calculate Gipuzkoa disposal without cost basis')

    disposed_amount = event.taxable_amount + event.free_amount
    disposal_value_eur = disposed_amount * event.price
    acquisition_cost_eur = get_gipuzkoa_acquisition_cost_eur(event.cost_basis)

    return calculate_gipuzkoa_disposal(
        disposal_value_eur=disposal_value_eur,
        acquisition_cost_eur=acquisition_cost_eur,
        disposal_expenses_eur=disposal_expenses_eur,
    )
