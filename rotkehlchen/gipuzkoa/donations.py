from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, Mapping

from rotkehlchen.gipuzkoa.history import get_gipuzkoa_history_metadata

if TYPE_CHECKING:
    from rotkehlchen.accounting.structures.processed_event import ProcessedAccountingEvent
    from rotkehlchen.history.events.structures.base import HistoryBaseEntry


@dataclass(frozen=True)
class GipuzkoaDonationReview:
    """Donation linked to an accounting event that requires dedicated tax review."""

    originating_event_id: int
    tax_year: int
    fiscal_classification: str

    def serialize(self) -> dict[str, int | str]:
        """Serialize a donation review record."""
        return {
            'originating_event_id': self.originating_event_id,
            'tax_year': self.tax_year,
            'fiscal_classification': self.fiscal_classification,
        }


def collect_gipuzkoa_donation_reviews(
        events: Iterable[ProcessedAccountingEvent],
        history_events_by_id: Mapping[int, HistoryBaseEntry],
) -> list[GipuzkoaDonationReview]:
    """Collect linked Gipuzkoa donation events for dedicated tax review."""
    reviews = []

    for event in events:
        originating_event_id = event.extra_data.get('originating_event_id')
        if not isinstance(originating_event_id, int):
            continue

        history_event = history_events_by_id.get(originating_event_id)
        if history_event is None:
            continue

        metadata = get_gipuzkoa_history_metadata(history_event)
        if metadata['technical_classification'] != 'donation':
            continue

        reviews.append(GipuzkoaDonationReview(
            originating_event_id=originating_event_id,
            tax_year=metadata['tax_year'],
            fiscal_classification=metadata['fiscal_classification'],
        ))

    return reviews
