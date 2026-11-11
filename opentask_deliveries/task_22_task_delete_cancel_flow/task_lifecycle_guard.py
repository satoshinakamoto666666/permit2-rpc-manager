"""
Task Delete/Cancel Lifecycle Guard (`cmlaeupf50009jj048zqsrv7w`)
================================================================
Enforces owner-only / admin-only delete and cancel permissions:
- Tasks with 0 bids and 0 contracts can be hard-deleted or cancelled.
- Tasks with active bids or contracts CANNOT be hard-deleted; they transition
  to `status: "cancelled"` while preserving an immutable audit record
  (`actor_id`, `timestamp`, `reason`, `action`).
- Cancelled tasks are excluded from default browse queries unless `include_cancelled=True`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class TaskAuditRecord:
    task_id: str
    action: str  # "deleted" or "cancelled"
    actor_id: str
    reason: str
    timestamp: str


class TaskLifecycleManager:
    def __init__(self) -> None:
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.audit_log: List[TaskAuditRecord] = []

    def add_task(self, task_id: str, owner_id: str, title: str, active_bids: int = 0, active_contracts: int = 0) -> None:
        self.tasks[task_id] = {
            "id": task_id,
            "owner_id": owner_id,
            "title": title,
            "status": "open",
            "active_bids": active_bids,
            "active_contracts": active_contracts,
        }

    def delete_or_cancel_task(
        self,
        task_id: str,
        actor_id: str,
        reason: str,
        is_admin: bool = False,
        prefer_hard_delete: bool = False,
    ) -> Dict[str, Any]:
        if task_id not in self.tasks:
            raise KeyError(f"Task {task_id} not found")
        task = self.tasks[task_id]
        if not is_admin and task["owner_id"] != actor_id:
            raise PermissionError("Only the task owner or an admin can cancel or delete this task")
        if not reason or not reason.strip():
            raise ValueError("A non-empty cancellation/deletion reason is required for the audit log")

        now_iso = datetime.now(timezone.utc).isoformat()
        has_activity = task["active_bids"] > 0 or task["active_contracts"] > 0

        if prefer_hard_delete and has_activity:
            # Automatically downgrade to safe cancellation when bids/contracts exist
            action = "cancelled"
            task["status"] = "cancelled"
            task["cancelled_reason"] = reason.strip()
            task["cancelled_by"] = actor_id
            task["cancelled_at"] = now_iso
        elif prefer_hard_delete and not has_activity:
            action = "deleted"
            del self.tasks[task_id]
        else:
            action = "cancelled"
            task["status"] = "cancelled"
            task["cancelled_reason"] = reason.strip()
            task["cancelled_by"] = actor_id
            task["cancelled_at"] = now_iso

        record = TaskAuditRecord(
            task_id=task_id,
            action=action,
            actor_id=actor_id,
            reason=reason.strip(),
            timestamp=now_iso,
        )
        self.audit_log.append(record)
        return {"task_id": task_id, "action": action, "audit": record.__dict__}

    def browse_tasks(self, include_cancelled: bool = False) -> List[Dict[str, Any]]:
        return [
            t
            for t in self.tasks.values()
            if include_cancelled or t.get("status") != "cancelled"
        ]
