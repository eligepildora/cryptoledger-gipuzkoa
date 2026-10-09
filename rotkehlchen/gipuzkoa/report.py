from typing import TYPE_CHECKING, Any

from rotkehlchen.constants.assets import A_EUR
from rotkehlchen.errors.misc import InputError
from rotkehlchen.gipuzkoa.summary import aggregate_gipuzkoa_processed_disposals

if TYPE_CHECKING:
    from rotkehlchen.db.reports import DBAccountingReports


def get_gipuzkoa_report_summary(
        dbreport: 'DBAccountingReports',
        report_id: int,
) -> list[dict[str, Any]]:
    """Calculate Gipuzkoa annual disposal summaries from a persisted PnL report.

    The report must exist, be completely processed and use EUR as its profit
    currency. All persisted accounting events are loaded without API filtering
    or pagination before calculating the fiscal summaries.
    """
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

    summaries = aggregate_gipuzkoa_processed_disposals(
        events=dbreport.get_report_data_unfiltered(report_id),
        main_currency=A_EUR,
    )
    return [summaries[tax_year].serialize() for tax_year in sorted(summaries)]
