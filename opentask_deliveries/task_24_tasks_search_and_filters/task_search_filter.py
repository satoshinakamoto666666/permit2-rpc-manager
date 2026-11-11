"""
Server-Side Tasks Search, Filter & URL Query State Engine (`cmladrwc5000fjg040etsyw7v`)
======================================================================================
Dependency-free search & filter engine for `/tasks` supporting:
- Keyword search across `title` and `description`
- Filters: `skill` tag, `budget` text match, `status` (`open`/`active`/`closed`)
- Sort order: `newest` / `oldest`
- Bidirectional URL query-string serialization (`?q=...&skill=...&status=...&sort=...`)
"""

from __future__ import annotations

import urllib.parse
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class TaskFilterState:
    q: str = ""
    skill: str = ""
    budget: str = ""
    status: str = "open"
    sort: str = "newest"

    @classmethod
    def from_query_string(cls, query_string: str) -> "TaskFilterState":
        params = urllib.parse.parse_qs(query_string.lstrip("?"), keep_blank_values=False)
        return cls(
            q=params.get("q", [""])[0].strip(),
            skill=params.get("skill", [""])[0].strip(),
            budget=params.get("budget", [""])[0].strip(),
            status=params.get("status", ["open"])[0].strip().lower(),
            sort=params.get("sort", ["newest"])[0].strip().lower(),
        )

    def to_query_string(self) -> str:
        pairs = []
        if self.q:
            pairs.append(("q", self.q))
        if self.skill:
            pairs.append(("skill", self.skill))
        if self.budget:
            pairs.append(("budget", self.budget))
        if self.status:
            pairs.append(("status", self.status))
        if self.sort:
            pairs.append(("sort", self.sort))
        return "?" + urllib.parse.urlencode(pairs) if pairs else ""


def filter_and_sort_tasks(tasks: List[Dict[str, Any]], state: TaskFilterState) -> Dict[str, Any]:
    q_low = state.q.lower()
    skill_low = state.skill.lower()
    budget_low = state.budget.lower()
    status_low = state.status.lower()

    matched: List[Dict[str, Any]] = []
    for t in tasks:
        if status_low and status_low != "all" and (t.get("status") or "open").lower() != status_low:
            continue
        if q_low:
            haystack = f"{t.get('title', '')} {t.get('description', '')}".lower()
            if q_low not in haystack:
                continue
        if skill_low:
            tags = [str(tag).lower() for tag in t.get("skillsTags", [])]
            if skill_low not in tags:
                continue
        if budget_low:
            btext = f"{t.get('budgetText', '')} {t.get('budgetAmount', '')} {t.get('budgetCurrency', '')}".lower()
            if budget_low not in btext:
                continue
        matched.append(t)

    reverse = state.sort != "oldest"
    matched.sort(key=lambda x: x.get("createdAt", ""), reverse=reverse)
    return {
        "tasks": matched,
        "count": len(matched),
        "empty_state": len(matched) == 0,
        "url_query": state.to_query_string(),
    }
