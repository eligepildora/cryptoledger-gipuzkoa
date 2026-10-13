from typing import TYPE_CHECKING, Any

from rotkehlchen.constants.assets import A_EUR
from rotkehlchen.db.filtering import HistoryEventFilterQuery
from rotkehlchen.db.history_events import DBHistoryEvents
from rotkehlchen.errors.misc import InputError
from rotkehlchen.gipuzkoa.defi import collect_gipuzkoa_defi_reviews
from rotkehlchen.gipuzkoa.donations import collect_gipuzkoa_donation_reviews
from rotkehlchen.gipuzkoa.income import collect_gipuzkoa_income_reviews
from rotkehlchen.gipuzkoa.losses import collect_gipuzkoa_loss_reviews
from rotkehlchen.gipuzkoa.nft import collect_gipuzkoa_nft_reviews
from rotkehlchen.gipuzkoa.summary import aggregate_gipuzkoa_processed_disposals

if TYPE_CHECKING:
    from rotkehlchen.accounting.structures.processed_event import ProcessedAccountingEvent
    from rotkehlchen.db.reports import DBAccountingReports
    from rotkehlchen.history.events.structures.base import HistoryBaseEntry


def _load_gipuzkoa_report_context(
        dbreport: 'DBAccountingReports',
        report_id: int,
) -> tuple[list['ProcessedAccountingEvent'], dict[int, 'HistoryBaseEntry']]:
    """Load and validate persisted accounting and linked history events."""
    reports, _ = dbreport.get_reports(report_id=report_id, limit=1)
    if len(reports) == 0:
        raise InputError(f'PnL report with id {report_id} does not exist')

    report = reports[0]
    if report['processed_actions'] != report['total_actions']:
        raise ValueError(
            f'Cannot calculate Gipuzkoa summary from incomplete report {report_id}',
        )

    profit_currency = report['settings'].get('profit_currency')
    if profit_currency != A_EUR.identifier:
        raise ValueError(
            f'Gipuzkoa report calculation requires EUR as profit currency. '
            f'Report {report_id} uses {profit_currency}',
        )

    processed_events = dbreport.get_report_data_unfiltered(report_id)
    originating_event_ids = {
        originating_event_id
        for event in processed_events
        if isinstance(
            originating_event_id := event.extra_data.get('originating_event_id'),
            int,
        )
    }

    history_events_by_id = {}
    if originating_event_ids:
        dbhistory = DBHistoryEvents(dbreport.db)
        with dbreport.db.conn.read_ctx() as cursor:
            history_events = dbhistory.get_history_events_internal(
                cursor=cursor,
                filter_query=HistoryEventFilterQuery.make(
                    identifiers=sorted(originating_event_ids),
                ),
            )
        history_events_by_id = {
            event.identifier: event
            for event in history_events
            if event.identifier is not None
        }

    return processed_events, history_events_by_id


def get_gipuzkoa_report_summary(
        dbreport: 'DBAccountingReports',
        report_id: int,
) -> list[dict[str, Any]]:
    """Calculate Gipuzkoa annual disposal summaries from a persisted PnL report."""
    processed_events, history_events_by_id = _load_gipuzkoa_report_context(
        dbreport=dbreport,
        report_id=report_id,
    )

    summaries = aggregate_gipuzkoa_processed_disposals(
        events=processed_events,
        main_currency=A_EUR,
        history_events_by_id=history_events_by_id,
    )
    return [summaries[tax_year].serialize() for tax_year in sorted(summaries)]


def get_gipuzkoa_report_donation_reviews(
        dbreport: 'DBAccountingReports',
        report_id: int,
) -> list[dict[str, int | str]]:
    """Return donation events requiring dedicated Gipuzkoa tax review."""
    processed_events, history_events_by_id = _load_gipuzkoa_report_context(
        dbreport=dbreport,
        report_id=report_id,
    )

    reviews = collect_gipuzkoa_donation_reviews(
        events=processed_events,
        history_events_by_id=history_events_by_id,
    )
    return [review.serialize() for review in reviews]

def get_gipuzkoa_report_loss_reviews(
        dbreport: 'DBAccountingReports',
        report_id: int,
) -> list[dict[str, int | str]]:
    """Return loss events requiring dedicated Gipuzkoa tax review."""
    processed_events, history_events_by_id = _load_gipuzkoa_report_context(
        dbreport=dbreport,
        report_id=report_id,
    )

    reviews = collect_gipuzkoa_loss_reviews(
        events=processed_events,
        history_events_by_id=history_events_by_id,
    )
    return [review.serialize() for review in reviews]

def get_gipuzkoa_report_defi_reviews(
        dbreport: 'DBAccountingReports',
        report_id: int,
) -> list[dict[str, int | str]]:
    """Return DeFi events requiring dedicated Gipuzkoa protocol tax review."""
    processed_events, history_events_by_id = _load_gipuzkoa_report_context(
        dbreport=dbreport,
        report_id=report_id,
    )

    reviews = collect_gipuzkoa_defi_reviews(
        events=processed_events,
        history_events_by_id=history_events_by_id,
    )
    return [review.serialize() for review in reviews]

def get_gipuzkoa_report_nft_reviews(
        dbreport: 'DBAccountingReports',
        report_id: int,
) -> list[dict[str, int | str]]:
    """Return NFT events requiring dedicated Gipuzkoa transaction tax review."""
    processed_events, history_events_by_id = _load_gipuzkoa_report_context(
        dbreport=dbreport,
        report_id=report_id,
    )

    reviews = collect_gipuzkoa_nft_reviews(
        events=processed_events,
        history_events_by_id=history_events_by_id,
    )
    return [review.serialize() for review in reviews]

def get_gipuzkoa_report_income_reviews(
        dbreport: 'DBAccountingReports',
        report_id: int,
) -> list[dict[str, int | str]]:
    """Return income, staking and validator events requiring Gipuzkoa tax review."""
    processed_events, history_events_by_id = _load_gipuzkoa_report_context(
        dbreport=dbreport,
        report_id=report_id,
    )

    reviews = collect_gipuzkoa_income_reviews(
        events=processed_events,
        history_events_by_id=history_events_by_id,
    )
    return [review.serialize() for review in reviews]
