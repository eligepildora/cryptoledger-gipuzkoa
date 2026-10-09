from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
import requests

from rotkehlchen.accounting.constants import FREE_PNL_EVENTS_LIMIT
from rotkehlchen.accounting.cost_basis.base import (
    AssetAcquisitionEvent,
    CostBasisInfo,
    MatchedAcquisition,
)
from rotkehlchen.accounting.mixins.event import AccountingEventType
from rotkehlchen.accounting.pnl import PNL
from rotkehlchen.accounting.structures.processed_event import ProcessedAccountingEvent
from rotkehlchen.constants import ONE, ZERO
from rotkehlchen.constants.assets import A_DAI, A_ETH, A_EUR
from rotkehlchen.db.reports import DBAccountingReports
from rotkehlchen.db.settings import DBSettings
from rotkehlchen.errors.misc import InputError
from rotkehlchen.fval import FVal
from rotkehlchen.tests.utils.api import (
    api_url_for,
    assert_error_response,
    assert_proper_response,
)
from rotkehlchen.tests.utils.constants import A_GBP, TEST_PREMIUM_PNL_EVENTS_LIMIT
from rotkehlchen.types import Location, Price, Timestamp
from rotkehlchen.utils.misc import timestamp_to_date

if TYPE_CHECKING:
    from rotkehlchen.api.server import APIServer


def setup_report_events(database) -> tuple[int, list[ProcessedAccountingEvent]]:
    """Input events to the DB for testing"""
    timestamp_1_secs, timestamp_2_secs, eth_price_ts_1, eth_price_ts_2, half_amount, hundred = Timestamp(1741634066), Timestamp(1741634100), FVal('2000'), FVal('2200'), FVal(0.5), FVal('100')  # noqa: E501
    dbreport = DBAccountingReports(database)
    settings = DBSettings(
        main_currency=A_GBP,
        calculate_past_cost_basis=False,
        include_gas_costs=False,
        pnl_csv_have_summary=False,
        pnl_csv_with_formulas=True,
        taxfree_after_period=15,
    )

    report_id = dbreport.add_report(
        first_processed_timestamp=timestamp_1_secs,
        start_ts=timestamp_1_secs,
        end_ts=timestamp_2_secs,
        settings=settings,
    )

    events = [
        ProcessedAccountingEvent(
            event_type=AccountingEventType.TRANSACTION_EVENT,
            notes='Received 1 ETH',
            location=Location.ETHEREUM,
            timestamp=timestamp_1_secs,
            asset=A_ETH,
            free_amount=ONE,
            taxable_amount=ZERO,
            price=Price(eth_price_ts_1),
            pnl=PNL(free=ZERO, taxable=eth_price_ts_1),
            cost_basis=None,
            index=0,
            extra_data={},
        ), ProcessedAccountingEvent(
            event_type=AccountingEventType.TRANSACTION_EVENT,
            notes='Send 0.5 ETH to 0xABC',
            location=Location.ETHEREUM,
            timestamp=timestamp_2_secs,
            asset=A_ETH,
            free_amount=ZERO,
            taxable_amount=half_amount,
            price=Price(eth_price_ts_2),
            pnl=PNL(taxable=half_amount, free=ONE),
            cost_basis=None,
            index=1,
            extra_data={},
        ), ProcessedAccountingEvent(
            event_type=AccountingEventType.TRANSACTION_EVENT,
            notes='Received 100 DAI',
            location=Location.ETHEREUM,
            timestamp=timestamp_2_secs,
            asset=A_DAI,
            free_amount=hundred,
            taxable_amount=ZERO,
            price=Price(ONE),
            pnl=PNL(taxable=ZERO, free=hundred),
            cost_basis=None,
            index=0,
            extra_data={},
        ),
    ]

    for event in events:
        dbreport.add_report_data(
            report_id=report_id,
            time=event.timestamp,
            ts_converter=timestamp_to_date,
            event=event,
        )

    return report_id, events


@pytest.mark.parametrize('start_with_valid_premium', [True, False])
def test_get_report_data_with_premium(
        rotkehlchen_api_server: APIServer,
        start_with_valid_premium: bool,
) -> None:
    """Test that getting report data works correctly with premium subscription active"""
    # First create a report and add events
    report_id, events = setup_report_events(rotkehlchen_api_server.rest_api.rotkehlchen.data.db)

    # Query report data with no filters
    response = requests.post(
        api_url_for(rotkehlchen_api_server, 'per_report_data_resource', report_id=report_id),
    )
    assert_proper_response(response)
    data = response.json()
    assert data['message'] == ''
    assert 'entries' in data['result']
    assert 'entries_found' in data['result']
    assert 'entries_total' in data['result']
    assert 'entries_limit' in data['result']
    assert len(data['result']['entries']) == len(events)
    assert data['result']['entries_found'] == len(events)
    assert data['result']['entries_total'] == len(events)
    assert data['result']['entries_limit'] == TEST_PREMIUM_PNL_EVENTS_LIMIT if start_with_valid_premium else FREE_PNL_EVENTS_LIMIT  # noqa: E501

    # Test pagination limits
    response = requests.post(
        api_url_for(rotkehlchen_api_server, 'per_report_data_resource', report_id=report_id),
        json={'offset': 0, 'limit': 1},
    )
    assert_proper_response(response)
    data = response.json()
    assert len(data['result']['entries']) == 1
    assert data['result']['entries_found'] == len(events)
    assert data['result']['entries_total'] == len(events)
    assert data['result']['entries_limit'] == TEST_PREMIUM_PNL_EVENTS_LIMIT if start_with_valid_premium else FREE_PNL_EVENTS_LIMIT  # noqa: E501


def test_get_report_data_invalid_report(
        rotkehlchen_api_server: APIServer,
) -> None:
    """Test that requesting invalid report ID is handled correctly"""
    response = requests.post(
        api_url_for(rotkehlchen_api_server, 'per_report_data_resource', report_id=1),
    )
    assert_error_response(
        response=response,
        contained_in_msg='Tried to get PnL events from non existing report with id 1',
        status_code=HTTPStatus.BAD_REQUEST,
    )


def test_get_gipuzkoa_report_summary(
        rotkehlchen_api_server: APIServer,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = [{
        'tax_year': 2025,
        'total_disposal_value_eur': '5000',
        'total_acquisition_cost_eur': '3000',
        'total_disposal_expenses_eur': '100',
        'gross_gains_eur': '1900',
        'gross_losses_eur': '0',
        'net_gain_loss_eur': '1900',
        'disposal_count': 1,
    }]

    monkeypatch.setattr(
        'rotkehlchen.api.rest.get_gipuzkoa_report_summary',
        lambda dbreport, report_id: expected,
    )

    response = requests.get(
        api_url_for(
            rotkehlchen_api_server,
            'per_report_gipuzkoa_resource',
            report_id=42,
        ),
    )

    assert_proper_response(response)
    data = response.json()
    assert data['message'] == ''
    assert data['result'] == expected


@pytest.mark.parametrize(
    ('exception', 'expected_message'),
    [
        (
            InputError('PnL report with id 42 does not exist'),
            'PnL report with id 42 does not exist',
        ),
        (
            ValueError('Cannot calculate Gipuzkoa summary from incomplete report 42'),
            'Cannot calculate Gipuzkoa summary from incomplete report 42',
        ),
        (
            ValueError(
                'Gipuzkoa report calculation requires EUR as profit currency. '
                'Report 42 uses USD',
            ),
            'Gipuzkoa report calculation requires EUR as profit currency',
        ),
    ],
)
def test_get_gipuzkoa_report_summary_errors(
        rotkehlchen_api_server: APIServer,
        monkeypatch: pytest.MonkeyPatch,
        exception: Exception,
        expected_message: str,
) -> None:
    def raise_error(dbreport, report_id):
        raise exception

    monkeypatch.setattr(
        'rotkehlchen.api.rest.get_gipuzkoa_report_summary',
        raise_error,
    )

    response = requests.get(
        api_url_for(
            rotkehlchen_api_server,
            'per_report_gipuzkoa_resource',
            report_id=42,
        ),
    )

    assert_error_response(
        response=response,
        contained_in_msg=expected_message,
        status_code=HTTPStatus.BAD_REQUEST,
    )

def test_get_gipuzkoa_report_summary_end_to_end(
        rotkehlchen_api_server: APIServer,
) -> None:
    database = rotkehlchen_api_server.rest_api.rotkehlchen.data.db
    dbreport = DBAccountingReports(database)
    acquisition_timestamp = Timestamp(1717200000)
    disposal_timestamp = Timestamp(1748736000)

    settings = DBSettings(
        main_currency=A_EUR,
        calculate_past_cost_basis=False,
        include_gas_costs=False,
        pnl_csv_have_summary=False,
        pnl_csv_with_formulas=True,
        taxfree_after_period=15,
    )
    report_id = dbreport.add_report(
        first_processed_timestamp=disposal_timestamp,
        start_ts=disposal_timestamp,
        end_ts=disposal_timestamp,
        settings=settings,
    )

    acquisition_event = AssetAcquisitionEvent(
        amount=FVal('2'),
        timestamp=acquisition_timestamp,
        rate=Price(FVal('1500')),
        index=0,
    )
    cost_basis = CostBasisInfo(
        taxable_amount=FVal('2'),
        taxable_bought_cost=FVal('3000'),
        taxfree_bought_cost=ZERO,
        matched_acquisitions=[
            MatchedAcquisition(
                amount=FVal('2'),
                event=acquisition_event,
                taxable=True,
            ),
        ],
        is_complete=True,
    )

    events = [
        ProcessedAccountingEvent(
            event_type=AccountingEventType.TRADE,
            notes='Gipuzkoa API disposal',
            location=Location.EXTERNAL,
            timestamp=disposal_timestamp,
            asset=A_ETH,
            free_amount=ZERO,
            taxable_amount=FVal('2'),
            price=Price(FVal('2500')),
            pnl=PNL(),
            cost_basis=cost_basis,
            index=0,
            extra_data={
                'direction': 'out',
                'group_id': 'gipuzkoa-api-swap',
            },
        ),
        ProcessedAccountingEvent(
            event_type=AccountingEventType.FEE,
            notes='Gipuzkoa API disposal fee',
            location=Location.EXTERNAL,
            timestamp=disposal_timestamp,
            asset=A_ETH,
            free_amount=ZERO,
            taxable_amount=FVal('0.04'),
            price=Price(FVal('2500')),
            pnl=PNL(),
            cost_basis=None,
            index=1,
            extra_data={
                'direction': 'out',
                'group_id': 'gipuzkoa-api-swap',
            },
        ),
    ]

    for event in events:
        dbreport.add_report_data(
            report_id=report_id,
            time=event.timestamp,
            ts_converter=timestamp_to_date,
            event=event,
        )

    response = requests.get(
        api_url_for(
            rotkehlchen_api_server,
            'per_report_gipuzkoa_resource',
            report_id=report_id,
        ),
    )

    assert_proper_response(response)
    data = response.json()
    assert data['message'] == ''
    assert data['result'] == [{
        'tax_year': 2025,
        'total_disposal_value_eur': '5000',
        'total_acquisition_cost_eur': '3000',
        'total_disposal_expenses_eur': '100',
        'gross_gains_eur': '1900',
        'gross_losses_eur': '0',
        'net_gain_loss_eur': '1900',
        'disposal_count': 1,
    }]
