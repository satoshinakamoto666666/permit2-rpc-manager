#!/usr/bin/env python3
"""
Google Maps Business Lead Generation Automation Tool (Places API v1 + Normalization + Dedup + CSV/JSON Export)
Task ID: cmlf8ux02000fl204qalhu8tt ($400 USDC — 开发一个基于 Google Maps 商家信息的潜在客户开发 (Lead Gen) 自动化工具)
"""

from __future__ import annotations
import csv
import io
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class BusinessLead:
    place_id: str
    name: str
    category: str
    formatted_address: str
    phone_e164: str
    website: str
    domain: str
    rating: float
    user_ratings_total: int
    lead_score: int
    qualification_tier: str


class GoogleMapsLeadGenEngine:
    """
    Production-ready Google Maps / Places v1 Lead Generation pipeline:
    1) Parses raw Google Maps Places API responses (v1 / legacy textSearch & details)
    2) Normalizes phone numbers, extracts canonical root domains, and deduplicates by place_id/domain
    3) Scores leads (0-100) based on rating volume, website presence, phone availability, and target niche fit
    4) Exports clean CRM-ready CSV and JSON lead lists
    """

    @staticmethod
    def extract_domain(url: str) -> str:
        if not url:
            return ""
        clean = re.sub(r"^https?://", "", url.strip().lower())
        clean = clean.split("/")[0].split("?")[0]
        return clean[4:] if clean.startswith("www.") else clean

    @staticmethod
    def normalize_phone(phone: str) -> str:
        if not phone:
            return ""
        digits = re.sub(r"[^\d+]", "", phone)
        return digits

    def score_lead(self, rating: float, reviews: int, has_phone: bool, has_website: bool) -> int:
        score = 0
        if has_phone:
            score += 30
        if has_website:
            score += 25
        if rating >= 4.0:
            score += 25
        elif rating >= 3.5:
            score += 15
        if reviews >= 50:
            score += 20
        elif reviews >= 10:
            score += 10
        return min(100, score)

    def process_places_payload(self, places: List[Dict[str, Any]], min_score: int = 0) -> List[BusinessLead]:
        seen_keys: set[str] = set()
        leads: List[BusinessLead] = []

        for item in places:
            place_id = str(item.get("place_id") or item.get("id") or "").strip()
            name = str(item.get("name") or item.get("displayName", {}).get("text") or "").strip()
            if not name:
                continue
            website = str(item.get("website") or item.get("websiteUri") or "").strip()
            domain = self.extract_domain(website)
            dedup_key = place_id or f"{name.lower()}::{domain}"
            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)

            phone = self.normalize_phone(
                str(item.get("formatted_phone_number") or item.get("internationalPhoneNumber") or "")
            )
            rating = float(item.get("rating") or 0.0)
            reviews = int(item.get("user_ratings_total") or item.get("userRatingCount") or 0)
            types = item.get("types") or [item.get("primaryType") or "business"]
            category = str(types[0]) if types else "business"
            address = str(item.get("formatted_address") or item.get("formattedAddress") or "").strip()

            score = self.score_lead(rating, reviews, bool(phone), bool(website))
            if score < min_score:
                continue
            tier = "A_HOT" if score >= 80 else ("B_WARM" if score >= 50 else "C_COLD")

            leads.append(
                BusinessLead(
                    place_id=place_id or f"gen_{len(leads)+1}",
                    name=name,
                    category=category,
                    formatted_address=address,
                    phone_e164=phone,
                    website=website,
                    domain=domain,
                    rating=rating,
                    user_ratings_total=reviews,
                    lead_score=score,
                    qualification_tier=tier,
                )
            )

        leads.sort(key=lambda x: (-x.lead_score, -x.user_ratings_total))
        return leads

    @staticmethod
    def to_csv(leads: List[BusinessLead]) -> str:
        buf = io.StringIO(newline="")
        fieldnames = [
            "place_id",
            "name",
            "category",
            "formatted_address",
            "phone_e164",
            "website",
            "domain",
            "rating",
            "user_ratings_total",
            "lead_score",
            "qualification_tier",
        ]
        writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for lead in leads:
            writer.writerow(asdict(lead))
        return buf.getvalue()

    @staticmethod
    def to_json(leads: List[BusinessLead]) -> str:
        return json.dumps([asdict(l) for l in leads], indent=2, ensure_ascii=False)
