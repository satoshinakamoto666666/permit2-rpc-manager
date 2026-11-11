"""
Observation Deck v1 — Human Ops Dashboard for Monitoring Agent Work (`cmlaexl31000njg04s46ystuz`)
=================================================================================================
Provides an access-controlled (admin/allowlist), read-only operational dashboard with:
- 4 Overview Cards: #open tasks, #active contracts, #deliverables pending review, #disputes
- 4 Deep-Linked Tables: Recent tasks, Recent bids, Active contracts, Deliverables submitted
- Status filter + keyword search across agent handle and task title
"""

from __future__ import annotations

import html
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


@dataclass
class ObservationDeckService:
    allowlisted_handles: Set[str] = field(default_factory=lambda: {"admin", "ops_lead", "keystone_mod"})

    def check_access(self, actor_handle: str, is_admin: bool = False) -> bool:
        return bool(is_admin or actor_handle in self.allowlisted_handles)

    def build_dashboard_view(
        self,
        actor_handle: str,
        is_admin: bool,
        tasks: List[Dict[str, Any]],
        bids: List[Dict[str, Any]],
        contracts: List[Dict[str, Any]],
        deliverables: List[Dict[str, Any]],
        status_filter: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not self.check_access(actor_handle, is_admin=is_admin):
            raise PermissionError(f"Access denied to Observation Deck v1 for actor '{actor_handle}'")

        q = (search_query or "").strip().lower()
        st = (status_filter or "").strip().lower()

        def match_row(text_fields: List[str], row_status: str) -> bool:
            if st and row_status.lower() != st:
                return False
            if q and not any(q in (f or "").lower() for f in text_fields):
                return False
            return True

        overview_cards = {
            "open_tasks_count": sum(1 for t in tasks if t.get("status") == "open"),
            "active_contracts_count": sum(1 for c in contracts if c.get("status") == "active"),
            "deliverables_pending_review_count": sum(1 for d in deliverables if d.get("needs_action", True)),
            "disputes_count": sum(1 for c in contracts if c.get("status") == "disputed"),
        }

        filtered_tasks = [
            {
                **t,
                "deep_link": f"/tasks/{t['id']}",
            }
            for t in tasks
            if match_row([t.get("title", ""), t.get("owner", "")], t.get("status", ""))
        ]
        filtered_bids = [
            {
                **b,
                "deep_link": f"/tasks/{b['task_id']}#bid-{b['id']}",
            }
            for b in bids
            if match_row([b.get("task_title", ""), b.get("bidder", "")], b.get("status", "active"))
        ]
        filtered_contracts = [
            {
                **c,
                "deep_link": f"/contracts/{c['id']}",
            }
            for c in contracts
            if match_row([c.get("buyer", ""), c.get("seller", "")], c.get("status", ""))
        ]
        filtered_deliverables = [
            {
                **d,
                "deep_link": f"/contracts/{d['contract_id']}/deliveries/{d['id']}",
            }
            for d in deliverables
            if match_row([d.get("title", ""), d.get("seller", "")], "pending_review" if d.get("needs_action") else "reviewed")
        ]

        return {
            "route": "/admin/observation-deck",
            "overview_cards": overview_cards,
            "tables": {
                "recent_tasks": filtered_tasks,
                "recent_bids": filtered_bids,
                "active_contracts": filtered_contracts,
                "deliverables_submitted": filtered_deliverables,
            },
        }
