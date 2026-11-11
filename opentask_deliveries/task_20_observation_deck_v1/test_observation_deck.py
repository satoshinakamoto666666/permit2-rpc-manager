import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from observation_deck import ObservationDeckService


def test_observation_deck_access_and_cards():
    svc = ObservationDeckService()
    with pytest.raises(PermissionError):
        svc.build_dashboard_view("anonymous_user", False, [], [], [], [])

    view = svc.build_dashboard_view(
        actor_handle="admin",
        is_admin=True,
        tasks=[{"id": "t1", "title": "Build parser", "status": "open", "owner": "alice", "createdAt": "2026-11-10"}],
        bids=[{"id": "b1", "task_id": "t1", "task_title": "Build parser", "bidder": "bot_1", "price": "100 USDC", "eta": 1}],
        contracts=[{"id": "c1", "status": "active", "buyer": "alice", "seller": "bot_1", "lastActivity": "2026-11-10"}],
        deliverables=[{"id": "d1", "contract_id": "c1", "title": "Parser PR", "seller": "bot_1", "needs_action": True}],
        search_query="parser",
    )
    assert view["overview_cards"]["open_tasks_count"] == 1
    assert view["overview_cards"]["active_contracts_count"] == 1
    assert view["overview_cards"]["deliverables_pending_review_count"] == 1
    assert view["tables"]["recent_tasks"][0]["deep_link"] == "/tasks/t1"
