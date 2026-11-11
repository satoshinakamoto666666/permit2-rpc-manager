import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from task_lifecycle_guard import TaskLifecycleManager


def test_task_delete_and_cancel_rules():
    mgr = TaskLifecycleManager()
    mgr.add_task("t_empty", owner_id="user_1", title="Draft task", active_bids=0)
    mgr.add_task("t_active", owner_id="user_1", title="Bidded task", active_bids=2)

    with pytest.raises(PermissionError):
        mgr.delete_or_cancel_task("t_empty", actor_id="intruder", reason="spam")

    # Task with active bids cannot be hard-deleted -> safely cancelled instead
    res1 = mgr.delete_or_cancel_task("t_active", actor_id="user_1", reason="Scope changed", prefer_hard_delete=True)
    assert res1["action"] == "cancelled"
    assert len(mgr.browse_tasks(include_cancelled=False)) == 1

    # Task with 0 bids can be hard-deleted
    res2 = mgr.delete_or_cancel_task("t_empty", actor_id="user_1", reason="Mistake", prefer_hard_delete=True)
    assert res2["action"] == "deleted"
    assert len(mgr.audit_log) == 2
