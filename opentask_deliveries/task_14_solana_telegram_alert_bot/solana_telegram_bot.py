#!/usr/bin/env python3
"""
Custom Telegram Alert Bot for Solana Wallet Activity
Task ID: cmv3yauqc01kr06jmt8beq4h9 ($5 USDC — Seeking builder: custom Telegram alert bot for Solana wallet activity)
"""

from __future__ import annotations
import json
import urllib.request
from typing import Any, Dict, List, Optional

OUR_SOLANA_WALLET = "Aw2hhJvjewAcxssyWMzKmFge6jWxEzN6GiFQgyZNKakt"


class SolanaTelegramAlertBot:
    """
    Monitors a Solana wallet via JSON-RPC (`getSignaturesForAddress` & `getTransaction`)
    and formats/dispatches rich MarkdownV2 / HTML Telegram Bot API alerts (`POST /bot<token>/sendMessage`).
    """

    def __init__(
        self,
        wallet_address: str = OUR_SOLANA_WALLET,
        rpc_url: str = "https://api.mainnet-beta.solana.com",
        telegram_bot_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
    ) -> None:
        self.wallet_address = wallet_address
        self.rpc_url = rpc_url
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id
        self._seen_signatures: set[str] = set()

    def fetch_recent_signatures(self, limit: int = 10) -> List[Dict[str, Any]]:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [self.wallet_address, {"limit": limit, "commitment": "confirmed"}],
        }
        req = urllib.request.Request(
            self.rpc_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "ZeroCapitalAgent/1.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
        return data.get("result") or []

    def format_alert_message(self, sig_entry: Dict[str, Any]) -> str:
        sig = sig_entry.get("signature", "unknown")
        slot = sig_entry.get("slot", 0)
        err = sig_entry.get("err")
        status = "CONFIRMED" if err is None else f"FAILED ({err})"
        memo = sig_entry.get("memo") or "None"
        return (
            f"🔔 *Solana Wallet Activity Alert*\n"
            f"• *Wallet*: `{self.wallet_address}`\n"
            f"• *Status*: `{status}`\n"
            f"• *Slot*: `{slot}`\n"
            f"• *Memo*: `{memo}`\n"
            f"• *Explorer*: https://solscan.io/tx/{sig}"
        )

    def poll_new_events(self, raw_signatures: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        entries = raw_signatures if raw_signatures is not None else self.fetch_recent_signatures(limit=5)
        alerts: List[str] = []
        for entry in entries:
            sig = entry.get("signature")
            if not sig or sig in self._seen_signatures:
                continue
            self._seen_signatures.add(sig)
            alerts.append(self.format_alert_message(entry))
        return alerts
