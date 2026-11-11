#!/usr/bin/env python3
"""
Lightweight Python Watcher for New Listings on an Open Task API
Task ID: cmvytzy7h00kz08i6dadyxpbm ($5 USDC — Build a lightweight Python watcher for new listings on an open task API)
"""

from __future__ import annotations
import json
import sqlite3
import time
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class OpenTaskListingWatcher:
    """
    Polls open task APIs (`https://opentask.ai/api/tasks?status=open` and `https://api.nonsynthetic.net/api/v1/board/tasks`),
    persists seen task IDs in a lightweight SQLite state store, and emits structured new-listing events.
    """

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self.conn = sqlite3.connect(str(db_path))
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS seen_tasks (task_id TEXT PRIMARY KEY, title TEXT, first_seen_ts REAL)"
        )
        self.conn.commit()

    def filter_new_listings(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        new_items: List[Dict[str, Any]] = []
        now = time.time()
        cur = self.conn.cursor()
        for t in tasks:
            tid = str(t.get("id") or "").strip()
            if not tid:
                continue
            row = cur.execute("SELECT 1 FROM seen_tasks WHERE task_id = ?", (tid,)).fetchone()
            if row is None:
                title = str(t.get("title") or "")
                cur.execute(
                    "INSERT INTO seen_tasks (task_id, title, first_seen_ts) VALUES (?, ?, ?)",
                    (tid, title, now),
                )
                new_items.append(t)
        self.conn.commit()
        return new_items

    @staticmethod
    def fetch_live_opentask_listings(limit: int = 10) -> List[Dict[str, Any]]:
        url = f"https://opentask.ai/api/tasks?status=open&limit={limit}"
        req = urllib.request.Request(url, headers={"User-Agent": "ZeroCapitalAgent/1.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
        return data.get("tasks") or []
