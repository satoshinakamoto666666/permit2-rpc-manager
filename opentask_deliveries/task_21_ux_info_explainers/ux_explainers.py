"""
UX Info/Explainer Patterns for Humans + Bots (`cmlaew6x8000djj04tekay5ec`)
==========================================================================
Accessible (`aria-label`, `role="tooltip"`, `tabindex="0"`) explainer definitions
and HTML helpers for Task page, Bid form, Contract delivery section, and Tokens page.
"""

from __future__ import annotations

import html
from typing import Dict, List

EXPLAINER_CATALOG: Dict[str, Dict[str, str]] = {
    "bid": {
        "surface": "Bid form & Task page",
        "title": "What is a Bid?",
        "copy": "A Bid is a non-binding offer proposing your price, estimated delivery time (ETA), and technical approach for an open task.",
    },
    "contract": {
        "surface": "Task page & Contract delivery section",
        "title": "What is a Contract?",
        "copy": "A Contract is created when a requester hires a winning bid, binding the agreed scope, payout method, and delivery milestones.",
    },
    "deliverable_url": {
        "surface": "Contract delivery section",
        "title": "What should Deliverable URL be?",
        "copy": "Provide a credential-free public HTTPS link (e.g., GitHub PR, commit, or artifact URL) plus a SHA-256 digest so the buyer can verify your work.",
    },
    "off_platform_payment": {
        "surface": "Task page & Contract delivery section",
        "title": "What does Non-Custodial / Off-Platform Payment mean?",
        "copy": "OpenTask does not custody funds; payments settle directly wallet-to-wallet via the non-custodial router and are verified on-chain.",
    },
    "api_token_scopes": {
        "surface": "Tokens page",
        "title": "What are API Tokens & Scopes?",
        "copy": "API Tokens and DPoP credentials grant bots least-privilege permissions (such as tasks:read, bids:write, deliveries:write) without exposing account passwords.",
    },
}


def render_accessible_explainer(key: str) -> str:
    if key not in EXPLAINER_CATALOG:
        raise KeyError(f"Unknown explainer key: {key}")
    item = EXPLAINER_CATALOG[key]
    title_esc = html.escape(item["title"])
    copy_esc = html.escape(item["copy"])
    return (
        f'<span class="ot-explainer" tabindex="0" role="button" aria-label="{title_esc}" '
        f'aria-describedby="tip-{key}">ⓘ'
        f'<span id="tip-{key}" role="tooltip" class="ot-tooltip">{copy_esc}</span>'
        f"</span>"
    )
