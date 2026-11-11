import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sheets_to_infinite_campus import SheetsToInfiniteCampusImporter


def test_sheets_to_infinite_campus_grade_sync():
    sample_csv = (
        "student_number,student_name,course_section_id,assignment_id,assignment_title,score_earned,points_possible\n"
        "100451,Alice Rivera,MATH-201,HW-04,Linear Systems Quiz,47.5,50\n"
        "100452,Marcus Vance,MATH-201,HW-04,Linear Systems Quiz,41.0,50\n"
    )
    importer = SheetsToInfiniteCampusImporter()
    records = importer.parse_gradebook_csv(sample_csv)
    assert len(records) == 2
    assert records[0].percentage == 95.0
    assert records[0].letter_grade == "A"
    assert records[1].percentage == 82.0
    assert records[1].letter_grade == "B"

    oneroster = json.loads(importer.to_infinite_campus_oneroster_json(records))
    assert oneroster["recordCount"] == 2
    assert oneroster["results"][0]["student"]["sourcedId"] == "100451"
    ic_csv = importer.to_infinite_campus_csv(records)
    assert "100451,Alice Rivera" in ic_csv
