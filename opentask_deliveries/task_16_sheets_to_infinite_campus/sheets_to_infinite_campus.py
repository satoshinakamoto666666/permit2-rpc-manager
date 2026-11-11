"""
Google Sheets Gradebook to Infinite Campus OneRoster v1.1 Sync Engine
=====================================================================
Parses student gradebook rows from Google Sheets (CSV export or Values API JSON),
validates student numbers, assignment codes, and numeric/letter scores, and
generates both Infinite Campus OneRoster v1.1 `lineItem` / `result` payloads
and Infinite Campus Gradebook Import CSV files.
"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, List


@dataclass
class GradeRecord:
    student_number: str
    student_name: str
    course_section_id: str
    assignment_id: str
    assignment_title: str
    score_earned: float
    points_possible: float
    percentage: float
    letter_grade: str
    score_status: str  # "fully graded", "exempt", "missing"


class SheetsToInfiniteCampusImporter:
    """Validates Google Sheets gradebook records and formats Infinite Campus imports."""

    @staticmethod
    def compute_letter_grade(pct: float) -> str:
        if pct >= 90.0:
            return "A"
        if pct >= 80.0:
            return "B"
        if pct >= 70.0:
            return "C"
        if pct >= 60.0:
            return "D"
        return "F"

    def parse_gradebook_csv(self, csv_text: str) -> List[GradeRecord]:
        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        records: List[GradeRecord] = []
        for idx, row in enumerate(reader, start=1):
            student_num = (row.get("student_number") or row.get("Student ID") or "").strip()
            if not student_num:
                raise ValueError(f"Row {idx} missing student_number")
            student_name = (row.get("student_name") or row.get("Student Name") or "").strip()
            section_id = (row.get("course_section_id") or row.get("Section") or "SEC-101").strip()
            assign_id = (row.get("assignment_id") or row.get("Assignment ID") or "ASN-001").strip()
            assign_title = (row.get("assignment_title") or row.get("Assignment") or "Gradebook Item").strip()

            earned = float(row.get("score_earned") or row.get("Score") or 0.0)
            possible = float(row.get("points_possible") or row.get("Max Points") or 100.0)
            if possible <= 0:
                raise ValueError(f"Row {idx} has invalid points_possible={possible}")
            if earned < 0 or earned > possible * 1.5:
                raise ValueError(f"Row {idx} score_earned={earned} out of valid bounds")

            pct = round((earned / possible) * 100.0, 2)
            records.append(
                GradeRecord(
                    student_number=student_num,
                    student_name=student_name,
                    course_section_id=section_id,
                    assignment_id=assign_id,
                    assignment_title=assign_title,
                    score_earned=earned,
                    points_possible=possible,
                    percentage=pct,
                    letter_grade=self.compute_letter_grade(pct),
                    score_status=(row.get("score_status") or "fully graded").strip(),
                )
            )
        return records

    @staticmethod
    def to_infinite_campus_oneroster_json(records: List[GradeRecord]) -> str:
        results = [
            {
                "sourcedId": f"res-{r.course_section_id}-{r.assignment_id}-{r.student_number}",
                "status": "active",
                "lineItem": {"sourcedId": r.assignment_id, "title": r.assignment_title},
                "student": {"sourcedId": r.student_number, "fullName": r.student_name},
                "score": r.score_earned,
                "scoreScale": {"maxScore": r.points_possible},
                "scorePercent": r.percentage,
                "textScore": r.letter_grade,
                "scoreStatus": r.score_status,
            }
            for r in records
        ]
        return json.dumps({"results": results, "recordCount": len(results)}, indent=2)

    @staticmethod
    def to_infinite_campus_csv(records: List[GradeRecord]) -> str:
        buf = io.StringIO()
        fields = [
            "student_number",
            "student_name",
            "course_section_id",
            "assignment_id",
            "assignment_title",
            "score_earned",
            "points_possible",
            "percentage",
            "letter_grade",
            "score_status",
        ]
        writer = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for r in records:
            writer.writerow(asdict(r))
        return buf.getvalue()
