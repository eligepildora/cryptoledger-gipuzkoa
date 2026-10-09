from rotkehlchen.fval import FVal
from rotkehlchen.gipuzkoa.calculation import calculate_gipuzkoa_disposal


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
