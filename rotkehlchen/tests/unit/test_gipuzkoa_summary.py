from types import SimpleNamespace

from rotkehlchen.accounting.mixins.event import AccountingEventType
from rotkehlchen.constants.assets import A_EUR
from rotkehlchen.fval import FVal
from rotkehlchen.gipuzkoa.calculation import calculate_gipuzkoa_disposal
from rotkehlchen.gipuzkoa.summary import (
    aggregate_gipuzkoa_disposals,
    aggregate_gipuzkoa_processed_disposals,
)
from rotkehlchen.history.events.structures.types import EventDirection
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
    assert summary.total_disposal_value_eur == FVal('15000')
    assert summary.total_acquisition_cost_eur == FVal('13000')
    assert summary.total_disposal_expenses_eur == FVal('150')
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


def test_gipuzkoa_processed_disposals_are_aggregated() -> None:
    event = SimpleNamespace(
        event_type=AccountingEventType.TRADE,
        extra_data={'direction': EventDirection.OUT.serialize()},
        timestamp=Timestamp(1748736000),
        taxable_amount=FVal('2'),
        free_amount=FVal('0'),
        price=FVal('2500'),
        cost_basis=SimpleNamespace(
            is_complete=True,
            matched_acquisitions=[
                SimpleNamespace(
                    amount=FVal('2'),
                    event=SimpleNamespace(rate=FVal('1500')),
                ),
            ],
        ),
    )

    summaries = aggregate_gipuzkoa_processed_disposals(
        events=[event],
        main_currency=A_EUR,
    )

    summary = summaries[2025]
    assert summary.gross_gains_eur == FVal('2000')
    assert summary.gross_losses_eur == FVal('0')
    assert summary.net_gain_loss_eur == FVal('2000')
    assert summary.disposal_count == 1


def test_gipuzkoa_processed_disposals_ignore_non_trade_out_events() -> None:
    cost_basis = SimpleNamespace(
        is_complete=True,
        matched_acquisitions=[
            SimpleNamespace(
                amount=FVal('1'),
                event=SimpleNamespace(rate=FVal('1000')),
            ),
        ],
    )

    trade_in = SimpleNamespace(
        event_type=AccountingEventType.TRADE,
        extra_data={'direction': EventDirection.IN.serialize()},
        timestamp=Timestamp(1748736000),
        taxable_amount=FVal('1'),
        free_amount=FVal('0'),
        price=FVal('2000'),
        cost_basis=cost_basis,
    )
    fee_out = SimpleNamespace(
        event_type=AccountingEventType.FEE,
        extra_data={'direction': EventDirection.OUT.serialize()},
        timestamp=Timestamp(1748736000),
        taxable_amount=FVal('1'),
        free_amount=FVal('0'),
        price=FVal('2000'),
        cost_basis=cost_basis,
    )

    summaries = aggregate_gipuzkoa_processed_disposals(
        events=[trade_in, fee_out],
        main_currency=A_EUR,
    )

    assert summaries == {}

def test_gipuzkoa_processed_disposal_uses_grouped_fee_as_expense() -> None:
    cost_basis = SimpleNamespace(
        is_complete=True,
        matched_acquisitions=[
            SimpleNamespace(
                amount=FVal('2'),
                event=SimpleNamespace(rate=FVal('1500')),
            ),
        ],
    )
    fee = SimpleNamespace(
        event_type=AccountingEventType.FEE,
        extra_data={
            'direction': EventDirection.OUT.serialize(),
            'group_id': 'swap-1',
        },
        timestamp=Timestamp(1748736000),
        taxable_amount=FVal('0'),
        free_amount=FVal('0.04'),
        price=FVal('2500'),
        cost_basis=None,
    )
    trade_out = SimpleNamespace(
        event_type=AccountingEventType.TRADE,
        extra_data={
            'direction': EventDirection.OUT.serialize(),
            'group_id': 'swap-1',
        },
        timestamp=Timestamp(1748736000),
        taxable_amount=FVal('2'),
        free_amount=FVal('0'),
        price=FVal('2500'),
        cost_basis=cost_basis,
    )

    summaries = aggregate_gipuzkoa_processed_disposals(
        events=[fee, trade_out],
        main_currency=A_EUR,
    )

    summary = summaries[2025]
    assert summary.total_disposal_value_eur == FVal('5000')
    assert summary.total_acquisition_cost_eur == FVal('3000')
    assert summary.total_disposal_expenses_eur == FVal('100')
    assert summary.gross_gains_eur == FVal('1900')
    assert summary.gross_losses_eur == FVal('0')
    assert summary.net_gain_loss_eur == FVal('1900')
    assert summary.disposal_count == 1

def test_gipuzkoa_processed_disposal_sums_multiple_grouped_fees() -> None:
    cost_basis = SimpleNamespace(
        is_complete=True,
        matched_acquisitions=[
            SimpleNamespace(
                amount=FVal('2'),
                event=SimpleNamespace(rate=FVal('1500')),
            ),
        ],
    )
    fee_one = SimpleNamespace(
        event_type=AccountingEventType.FEE,
        extra_data={
            'direction': EventDirection.OUT.serialize(),
            'group_id': 'swap-multi-fee',
        },
        timestamp=Timestamp(1748736000),
        taxable_amount=FVal('0'),
        free_amount=FVal('0.02'),
        price=FVal('2500'),
        cost_basis=None,
    )
    fee_two = SimpleNamespace(
        event_type=AccountingEventType.FEE,
        extra_data={
            'direction': EventDirection.OUT.serialize(),
            'group_id': 'swap-multi-fee',
        },
        timestamp=Timestamp(1748736000),
        taxable_amount=FVal('0.01'),
        free_amount=FVal('0'),
        price=FVal('2500'),
        cost_basis=None,
    )
    trade_out = SimpleNamespace(
        event_type=AccountingEventType.TRADE,
        extra_data={
            'direction': EventDirection.OUT.serialize(),
            'group_id': 'swap-multi-fee',
        },
        timestamp=Timestamp(1748736000),
        taxable_amount=FVal('2'),
        free_amount=FVal('0'),
        price=FVal('2500'),
        cost_basis=cost_basis,
    )

    summaries = aggregate_gipuzkoa_processed_disposals(
        events=[fee_one, trade_out, fee_two],
        main_currency=A_EUR,
    )

    summary = summaries[2025]
    assert summary.total_disposal_value_eur == FVal('5000')
    assert summary.total_acquisition_cost_eur == FVal('3000')
    assert summary.total_disposal_expenses_eur == FVal('75')
    assert summary.gross_gains_eur == FVal('1925')
    assert summary.net_gain_loss_eur == FVal('1925')
    assert summary.disposal_count == 1


def test_gipuzkoa_processed_disposal_ignores_fee_from_other_group() -> None:
    cost_basis = SimpleNamespace(
        is_complete=True,
        matched_acquisitions=[
            SimpleNamespace(
                amount=FVal('2'),
                event=SimpleNamespace(rate=FVal('1500')),
            ),
        ],
    )
    unrelated_fee = SimpleNamespace(
        event_type=AccountingEventType.FEE,
        extra_data={
            'direction': EventDirection.OUT.serialize(),
            'group_id': 'other-swap',
        },
        timestamp=Timestamp(1748736000),
        taxable_amount=FVal('0'),
        free_amount=FVal('0.04'),
        price=FVal('2500'),
        cost_basis=None,
    )
    trade_out = SimpleNamespace(
        event_type=AccountingEventType.TRADE,
        extra_data={
            'direction': EventDirection.OUT.serialize(),
            'group_id': 'target-swap',
        },
        timestamp=Timestamp(1748736000),
        taxable_amount=FVal('2'),
        free_amount=FVal('0'),
        price=FVal('2500'),
        cost_basis=cost_basis,
    )

    summaries = aggregate_gipuzkoa_processed_disposals(
        events=[unrelated_fee, trade_out],
        main_currency=A_EUR,
    )

    summary = summaries[2025]
    assert summary.gross_gains_eur == FVal('2000')
    assert summary.net_gain_loss_eur == FVal('2000')
    assert summary.disposal_count == 1
