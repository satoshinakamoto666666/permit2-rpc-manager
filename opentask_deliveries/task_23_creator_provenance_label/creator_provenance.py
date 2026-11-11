"""
Task Creator Provenance Resolver & Backfill Engine (`cmladxrkf000jjg04k67cafyl`)
===============================================================================
Fixes the "Created by human" label bug when agents post tasks via DPoP, MCP, or
scoped API tokens under a human-linked account by recording explicit request-level
`creatorProvenance` (`"agent" | "human"`) at task creation time and safely
backfilling legacy tasks.
"""

from __future__ import annotations

from typing import Any, Dict, List


def resolve_creator_provenance(auth_context: Dict[str, Any]) -> Dict[str, str]:
    """
    Determines whether a task was authored by an autonomous agent or a human browser
    session based on authentication mechanism (`dpop`, `api_token`, `mcp`, or `agent` profile).
    """
    auth_type = (auth_context.get("auth_type") or "session").lower()
    profile_kind = (auth_context.get("profile_kind") or "human").lower()
    user_agent = (auth_context.get("user_agent") or "").lower()

    if (
        auth_type in ("dpop", "api_token", "mcp", "a2a")
        or profile_kind == "agent"
        or "openclaw" in user_agent
        or "codex" in user_agent
    ):
        return {
            "creatorKind": "agent",
            "creatorAuthMethod": auth_type,
            "displayLabel": "Created by agent",
        }
    return {
        "creatorKind": "human",
        "creatorAuthMethod": auth_type,
        "displayLabel": "Created by human",
    }


def backfill_task_provenance(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    updated: List[Dict[str, Any]] = []
    for t in tasks:
        row = dict(t)
        if not row.get("creatorKind"):
            owner_kind = (row.get("owner", {}).get("kind") or "").lower()
            created_via = (row.get("createdVia") or "").lower()
            is_agent = owner_kind == "agent" or created_via in ("dpop", "api_token", "mcp", "openclaw")
            row["creatorKind"] = "agent" if is_agent else "human"
        row["displayLabel"] = "Created by agent" if row["creatorKind"] == "agent" else "Created by human"
        updated.append(row)
    return updated
