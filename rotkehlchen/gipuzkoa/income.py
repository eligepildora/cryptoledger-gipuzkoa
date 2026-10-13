from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, Mapping

from rotkehlchen.gipuzkoa.history import get_gipuzkoa_history_metadata

if TYPE_CHECKING:
    from rotkehlchen.accounting.structures.processed_event import ProcessedAccountingEvent
    from rotkehlchen.history.events.structures.base import HistoryBaseEntry


INCOME_REVIEW_CLASSIFICATIONS = frozenset({
    'income',
    'staking',
    'validator',
})


@dataclass(frozen=True)
class GipuzkoaIncomeReview:
    """Income-like event requiring dedicated Gipuzkoa tax review."""

    originating_event_id: int
    tax_year: int
    technical_classification: str
    fiscal_classification: str

    def serialize(self) -> dict[str, int | str]:
        """Serialize an income review record."""
        return {
            'originating_event_id': self.originating_event_id,
            'tax_year': self.tax_year,
            'technical_classification': self.technical_classification,
            'fiscal_classification': self.fiscal_classification,
        }


def collect_gipuzkoa_income_reviews(
        events: Iterable[ProcessedAccountingEvent],
        history_events_by_id: Mapping[int, HistoryBaseEntry],
) -> list[GipuzkoaIncomeReview]:
    """Collect linked income, staking and validator events for tax review."""
    reviews = []

    for event in events:
        originating_event_id = event.extra_data.get('originating_event_id')
        if not isinstance(originating_event_id, int):
            continue

        history_event = history_events_by_id.get(originating_event_id)
        if history_event is None:
            continue

        metadata = get_gipuzkoa_history_metadata(history_event)
        technical_classification = metadata['technical_classification']
        if technical_classification not in INCOME_REVIEW_CLASSIFICATIONS:
            continue

        reviews.append(GipuzkoaIncomeReview(
            originating_event_id=originating_event_id,
            tax_year=metadata['tax_year'],
            technical_classification=technical_classification,
            fiscal_classification=metadata['fiscal_classification'],
        ))

    return reviews
