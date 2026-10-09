from __future__ import annotations

from dataclasses import dataclass

from rotkehlchen.fval import FVal


@dataclass(frozen=True)
class GipuzkoaDisposalCalculation:
    """Result of a preliminary Gipuzkoa disposal calculation in EUR."""

    disposal_value_eur: FVal
    acquisition_cost_eur: FVal
    disposal_expenses_eur: FVal
    net_disposal_value_eur: FVal
    gain_loss_eur: FVal


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
