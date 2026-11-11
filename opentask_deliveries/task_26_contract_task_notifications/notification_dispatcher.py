"""
Contract & Task Event Notification Dispatcher (`cmladpyu7000bjg04cm7s2697`)
==========================================================================
Dispatches and persists in-app and optional email notifications for the 4 core
marketplace events:
1. `bid.created` -> notifies task owner
2. `contract.hired` -> notifies hired seller
3. `deliverable.submitted` -> notifies contract buyer
4. `contract.closed` -> notifies both seller and buyer
Includes deterministic `event_id` deduplication so retries never create duplicate alerts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set


@dataclass
class NotificationEvent:
    id: str
    recipient_id: str
    event_type: str
    title: str
    body: str
    deep_link: str
    created_at: str
    read: bool = False
    email_sent: bool = False


class NotificationDispatcher:
    def __init__(self, mailer: Optional[Callable[[str, str, str], bool]] = None) -> None:
        self.mailer = mailer
        self._inbox: Dict[str, List[NotificationEvent]] = {}
        self._seen_event_ids: Set[str] = set()

    def _emit(
        self,
        event_id: str,
        recipient_id: str,
        event_type: str,
        title: str,
        body: str,
        deep_link: str,
        timestamp: Optional[str] = None,
    ) -> Optional[NotificationEvent]:
        dedup_key = f"{event_id}:{recipient_id}"
        if dedup_key in self._seen_event_ids:
            return None
        self._seen_event_ids.add(dedup_key)

        now_iso = timestamp or datetime.now(timezone.utc).isoformat()
        email_ok = False
        if self.mailer is not None:
            email_ok = bool(self.mailer(recipient_id, title, f"{body}\nView: {deep_link}"))

        ev = NotificationEvent(
            id=event_id,
            recipient_id=recipient_id,
            event_type=event_type,
            title=title,
            body=body,
            deep_link=deep_link,
            created_at=now_iso,
            read=False,
            email_sent=email_ok,
        )
        self._inbox.setdefault(recipient_id, []).insert(0, ev)
        return ev

    def on_bid_created(self, bid_id: str, task_id: str, task_title: str, task_owner_id: str, bidder_handle: str, price_text: str) -> Optional[NotificationEvent]:
        return self._emit(
            event_id=f"evt-bid-{bid_id}",
            recipient_id=task_owner_id,
            event_type="bid.created",
            title=f"New bid on {task_title}",
            body=f"@{bidder_handle} submitted a bid for {price_text}.",
            deep_link=f"/tasks/{task_id}#bid-{bid_id}",
        )

    def on_contract_hired(self, contract_id: str, task_title: str, seller_id: str, buyer_handle: str) -> Optional[NotificationEvent]:
        return self._emit(
            event_id=f"evt-hire-{contract_id}",
            recipient_id=seller_id,
            event_type="contract.hired",
            title=f"You were hired for {task_title}",
            body=f"@{buyer_handle} created contract {contract_id}.",
            deep_link=f"/contracts/{contract_id}",
        )

    def on_deliverable_submitted(self, delivery_id: str, contract_id: str, task_title: str, buyer_id: str, seller_handle: str) -> Optional[NotificationEvent]:
        return self._emit(
            event_id=f"evt-deliv-{delivery_id}",
            recipient_id=buyer_id,
            event_type="deliverable.submitted",
            title=f"Deliverable submitted for {task_title}",
            body=f"@{seller_handle} submitted deliverable {delivery_id} for review.",
            deep_link=f"/contracts/{contract_id}/deliveries/{delivery_id}",
        )

    def on_contract_closed(self, contract_id: str, task_title: str, seller_id: str, buyer_id: str) -> List[NotificationEvent]:
        out = []
        for uid in (seller_id, buyer_id):
            ev = self._emit(
                event_id=f"evt-close-{contract_id}",
                recipient_id=uid,
                event_type="contract.closed",
                title=f"Contract accepted & closed: {task_title}",
                body=f"Contract {contract_id} has been accepted and closed.",
                deep_link=f"/contracts/{contract_id}",
            )
            if ev:
                out.append(ev)
        return out

    def list_notifications(self, recipient_id: str) -> List[Dict[str, Any]]:
        return [asdict(e) for e in self._inbox.get(recipient_id, [])]
