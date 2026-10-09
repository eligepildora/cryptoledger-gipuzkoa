from rotkehlchen.fval import FVal
from rotkehlchen.gipuzkoa.calculation import calculate_gipuzkoa_disposal
from rotkehlchen.gipuzkoa.summary import aggregate_gipuzkoa_disposals
from rotkehlchen.types import Timestamp


def test_gipuzkoa_annual_disposal_summary() -> None:
    gain = calculate_gipuzkoa_disposal(
        disposal_value_eur=FVal('10000'),
        acquisition_cost_eur=FVal('7000'),
        disposal_expenses_eur=FVal('100'),
    )
    loss = calculate_gipuzkoa_disposal(
        disposal_value_eur=FVal('5000'),
        acquisition_cost_eur=FVal('6000'),
        disposal_expenses_eur=FVal('50'),
    )

    summaries = aggregate_gipuzkoa_disposals([
        (Timestamp(1748736000), gain),
        (Timestamp(1748736000), loss),
    ])

    summary = summaries[2025]
    assert summary.gross_gains_eur == FVal('2900')
    assert summary.gross_losses_eur == FVal('1050')
    assert summary.net_gain_loss_eur == FVal('1850')
    assert summary.disposal_count == 2


def test_gipuzkoa_disposals_are_separated_by_tax_year() -> None:
    calculation = calculate_gipuzkoa_disposal(
        disposal_value_eur=FVal('2000'),
        acquisition_cost_eur=FVal('1000'),
        disposal_expenses_eur=FVal('0'),
    )

    summaries = aggregate_gipuzkoa_disposals([
        (Timestamp(1717200000), calculation),
        (Timestamp(1735687800), calculation),
    ])

    assert summaries[2024].net_gain_loss_eur == FVal('1000')
    assert summaries[2024].disposal_count == 1
    assert summaries[2025].net_gain_loss_eur == FVal('1000')
    assert summaries[2025].disposal_count == 1
