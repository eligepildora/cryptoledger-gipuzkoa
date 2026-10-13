from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, Mapping

from rotkehlchen.gipuzkoa.history import get_gipuzkoa_history_metadata

if TYPE_CHECKING:
    from rotkehlchen.accounting.structures.processed_event import ProcessedAccountingEvent
    from rotkehlchen.history.events.structures.base import HistoryBaseEntry


@dataclass(frozen=True)
class GipuzkoaDefiReview:
    """DeFi event linked to accounting data that requires protocol-level tax review."""

    originating_event_id: int
    tax_year: int
    fiscal_classification: str

    def serialize(self) -> dict[str, int | str]:
        """Serialize a DeFi review record."""
        return {
            'originating_event_id': self.originating_event_id,
            'tax_year': self.tax_year,
            'fiscal_classification': self.fiscal_classification,
        }


def collect_gipuzkoa_defi_reviews(
        events: Iterable[ProcessedAccountingEvent],
        history_events_by_id: Mapping[int, HistoryBaseEntry],
) -> list[GipuzkoaDefiReview]:
    """Collect linked Gipuzkoa DeFi events for dedicated protocol tax review."""
    reviews = []

    for event in events:
        originating_event_id = event.extra_data.get('originating_event_id')
        if not isinstance(originating_event_id, int):
            continue

        history_event = history_events_by_id.get(originating_event_id)
        if history_event is None:
            continue

        metadata = get_gipuzkoa_history_metadata(history_event)
        if metadata['technical_classification'] != 'defi':
            continue

        reviews.append(GipuzkoaDefiReview(
            originating_event_id=originating_event_id,
            tax_year=metadata['tax_year'],
            fiscal_classification=metadata['fiscal_classification'],
        ))

    return reviews
