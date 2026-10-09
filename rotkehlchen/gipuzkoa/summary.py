from dataclasses import dataclass
from typing import Iterable

from rotkehlchen.constants import ZERO
from rotkehlchen.fval import FVal
from rotkehlchen.gipuzkoa.calculation import GipuzkoaDisposalCalculation
from rotkehlchen.gipuzkoa.dates import get_gipuzkoa_tax_year
from rotkehlchen.types import Timestamp


@dataclass
class GipuzkoaAnnualDisposalSummary:
    """Aggregated cryptoasset disposal results for one Gipuzkoa tax year."""

    tax_year: int
    gross_gains_eur: FVal
    gross_losses_eur: FVal
    net_gain_loss_eur: FVal
    disposal_count: int


def aggregate_gipuzkoa_disposals(
        disposals: Iterable[tuple[Timestamp, GipuzkoaDisposalCalculation]],
) -> dict[int, GipuzkoaAnnualDisposalSummary]:
    """Aggregate calculated disposals by Gipuzkoa tax year."""
    summaries: dict[int, GipuzkoaAnnualDisposalSummary] = {}

    for timestamp, calculation in disposals:
        tax_year = get_gipuzkoa_tax_year(timestamp)
        summary = summaries.get(tax_year)

        if summary is None:
            summary = GipuzkoaAnnualDisposalSummary(
                tax_year=tax_year,
                gross_gains_eur=ZERO,
                gross_losses_eur=ZERO,
                net_gain_loss_eur=ZERO,
                disposal_count=0,
            )
            summaries[tax_year] = summary

        if calculation.gain_loss_eur >= ZERO:
            summary.gross_gains_eur += calculation.gain_loss_eur
        else:
            summary.gross_losses_eur += ZERO - calculation.gain_loss_eur

        summary.net_gain_loss_eur += calculation.gain_loss_eur
        summary.disposal_count += 1

    return summaries
