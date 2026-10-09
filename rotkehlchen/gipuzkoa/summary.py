from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable

from rotkehlchen.accounting.mixins.event import AccountingEventType
from rotkehlchen.constants import ZERO
from rotkehlchen.fval import FVal
from rotkehlchen.gipuzkoa.calculation import (
    GipuzkoaDisposalCalculation,
    calculate_gipuzkoa_processed_disposal,
)
from rotkehlchen.gipuzkoa.dates import get_gipuzkoa_tax_year
from rotkehlchen.history.events.structures.types import EventDirection
from rotkehlchen.types import Timestamp

if TYPE_CHECKING:
    from rotkehlchen.accounting.structures.processed_event import ProcessedAccountingEvent
    from rotkehlchen.assets.asset import Asset


@dataclass
class GipuzkoaAnnualDisposalSummary:
    """Aggregated cryptoasset disposal results for one Gipuzkoa tax year."""

    tax_year: int
    total_disposal_value_eur: FVal
    total_acquisition_cost_eur: FVal
    total_disposal_expenses_eur: FVal
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
                total_disposal_value_eur=ZERO,
                total_acquisition_cost_eur=ZERO,
                total_disposal_expenses_eur=ZERO,
                gross_gains_eur=ZERO,
                gross_losses_eur=ZERO,
                net_gain_loss_eur=ZERO,
                disposal_count=0,
            )
            summaries[tax_year] = summary

        summary.total_disposal_value_eur += calculation.disposal_value_eur
        summary.total_acquisition_cost_eur += calculation.acquisition_cost_eur
        summary.total_disposal_expenses_eur += calculation.disposal_expenses_eur

        if calculation.gain_loss_eur >= ZERO:
            summary.gross_gains_eur += calculation.gain_loss_eur
        else:
            summary.gross_losses_eur += ZERO - calculation.gain_loss_eur

        summary.net_gain_loss_eur += calculation.gain_loss_eur
        summary.disposal_count += 1

    return summaries


def aggregate_gipuzkoa_processed_disposals(
        events: Iterable[ProcessedAccountingEvent],
        main_currency: Asset,
) -> dict[int, GipuzkoaAnnualDisposalSummary]:
    """Calculate and aggregate processed disposal events by Gipuzkoa tax year."""
    processed_events = list(events)
    disposal_expenses_by_group: dict[str, FVal] = {}

    for event in processed_events:
        if (
            event.event_type != AccountingEventType.FEE or
            event.extra_data.get('direction') != EventDirection.OUT.serialize()
        ):
            continue

        group_id = event.extra_data.get('group_id')
        if not isinstance(group_id, str):
            continue

        fee_value_eur = (event.taxable_amount + event.free_amount) * event.price
        disposal_expenses_by_group[group_id] = (
            disposal_expenses_by_group.get(group_id, ZERO) + fee_value_eur
        )

    disposals = []
    for event in processed_events:
        if (
            event.event_type != AccountingEventType.TRADE or
            event.extra_data.get('direction') != EventDirection.OUT.serialize()
        ):
            continue

        group_id = event.extra_data.get('group_id')
        disposal_expenses_eur = (
            disposal_expenses_by_group.get(group_id, ZERO)
            if isinstance(group_id, str)
            else ZERO
        )
        calculation = calculate_gipuzkoa_processed_disposal(
            event=event,
            main_currency=main_currency,
            disposal_expenses_eur=disposal_expenses_eur,
        )
        disposals.append((event.timestamp, calculation))

    return aggregate_gipuzkoa_disposals(disposals)
