from types import SimpleNamespace

import pytest

from rotkehlchen.fval import FVal
from rotkehlchen.gipuzkoa.calculation import (
    calculate_gipuzkoa_disposal,
    get_gipuzkoa_acquisition_cost_eur,
)


def test_gipuzkoa_disposal_gain() -> None:
    result = calculate_gipuzkoa_disposal(
        disposal_value_eur=FVal('10000'),
        acquisition_cost_eur=FVal('7000'),
        disposal_expenses_eur=FVal('100'),
    )

    assert result.net_disposal_value_eur == FVal('9900')
    assert result.gain_loss_eur == FVal('2900')


def test_gipuzkoa_disposal_loss() -> None:
    result = calculate_gipuzkoa_disposal(
        disposal_value_eur=FVal('5000'),
        acquisition_cost_eur=FVal('6000'),
        disposal_expenses_eur=FVal('50'),
    )

    assert result.net_disposal_value_eur == FVal('4950')
    assert result.gain_loss_eur == FVal('-1050')


def test_gipuzkoa_acquisition_cost_from_matched_acquisitions() -> None:
    cost_basis = SimpleNamespace(
        is_complete=True,
        matched_acquisitions=[
            SimpleNamespace(
                amount=FVal('1.5'),
                event=SimpleNamespace(rate=FVal('2000')),
            ),
            SimpleNamespace(
                amount=FVal('0.25'),
                event=SimpleNamespace(rate=FVal('2400')),
            ),
        ],
    )

    assert get_gipuzkoa_acquisition_cost_eur(cost_basis) == FVal('3600')


def test_gipuzkoa_rejects_incomplete_cost_basis() -> None:
    cost_basis = SimpleNamespace(
        is_complete=False,
        matched_acquisitions=[],
    )

    with pytest.raises(
        ValueError,
        match='Cannot calculate Gipuzkoa acquisition cost from incomplete cost basis',
    ):
        get_gipuzkoa_acquisition_cost_eur(cost_basis)

