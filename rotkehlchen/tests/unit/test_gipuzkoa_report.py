from types import SimpleNamespace

import pytest

from rotkehlchen.accounting.mixins.event import AccountingEventType
from rotkehlchen.constants import ZERO
from rotkehlchen.constants.assets import A_EUR
from rotkehlchen.errors.misc import InputError
from rotkehlchen.fval import FVal
from rotkehlchen.gipuzkoa.report import get_gipuzkoa_report_summary
from rotkehlchen.types import Timestamp


def _make_report(
        *,
        processed_actions: int = 1,
        total_actions: int = 1,
        profit_currency: str = A_EUR.identifier,
) -> dict:
    return {
        'identifier': 1,
        'processed_actions': processed_actions,
        'total_actions': total_actions,
        'settings': {'profit_currency': profit_currency},
    }


def _make_disposal_event() -> SimpleNamespace:
    return SimpleNamespace(
        event_type=AccountingEventType.TRADE,
        extra_data={'direction': 'out'},
        timestamp=Timestamp(1748736000),
        taxable_amount=FVal('2'),
        free_amount=ZERO,
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


class FakeDBAccountingReports:

    def __init__(self, reports: list[dict], events: list[SimpleNamespace]) -> None:
        self.reports = reports
        self.events = events

    def get_reports(self, report_id: int, limit: int) -> tuple[list[dict], int]:
        return self.reports, len(self.reports)

    def get_report_data_unfiltered(self, report_id: int) -> list[SimpleNamespace]:
        return self.events


def test_gipuzkoa_report_summary() -> None:
    dbreport = FakeDBAccountingReports(
        reports=[_make_report()],
        events=[_make_disposal_event()],
    )

    result = get_gipuzkoa_report_summary(dbreport=dbreport, report_id=1)

    assert result == [{
        'tax_year': 2025,
        'total_disposal_value_eur': '5000',
        'total_acquisition_cost_eur': '3000',
        'total_disposal_expenses_eur': '0',
        'gross_gains_eur': '2000',
        'gross_losses_eur': '0',
        'net_gain_loss_eur': '2000',
        'disposal_count': 1,
    }]


def test_gipuzkoa_report_summary_rejects_missing_report() -> None:
    dbreport = FakeDBAccountingReports(reports=[], events=[])

    with pytest.raises(InputError, match='PnL report with id 1 does not exist'):
        get_gipuzkoa_report_summary(dbreport=dbreport, report_id=1)


def test_gipuzkoa_report_summary_rejects_incomplete_report() -> None:
    dbreport = FakeDBAccountingReports(
        reports=[_make_report(processed_actions=1, total_actions=2)],
        events=[],
    )

    with pytest.raises(
        ValueError,
        match='Cannot calculate Gipuzkoa summary from incomplete report 1',
    ):
        get_gipuzkoa_report_summary(dbreport=dbreport, report_id=1)


def test_gipuzkoa_report_summary_requires_eur() -> None:
    dbreport = FakeDBAccountingReports(
        reports=[_make_report(profit_currency='USD')],
        events=[],
    )

    with pytest.raises(
        ValueError,
        match='Gipuzkoa report calculation requires EUR as profit currency',
    ):
        get_gipuzkoa_report_summary(dbreport=dbreport, report_id=1)
