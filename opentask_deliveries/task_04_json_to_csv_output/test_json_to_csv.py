import csv
import json
from pathlib import Path
import pytest
from json_to_csv import convert_json_file_to_csv, json_objects_to_csv_string


def test_missing_keys_filled_with_empty_string(tmp_path: Path):
    sample_data = [
        {"id": 1, "name": "Alice", "role": "engineer"},
        {"id": 2, "name": "Bob", "department": "DeFi"},
        {"id": 3, "role": "auditor", "department": None, "bonus": 50},
    ]
    in_file = tmp_path / "input.json"
    out_file = tmp_path / "output.csv"
    in_file.write_text(json.dumps(sample_data), encoding="utf-8")

    count = convert_json_file_to_csv(in_file, out_file)
    assert count == 3

    rows = list(csv.DictReader(out_file.read_text(encoding="utf-8").splitlines()))
    assert len(rows) == 3
    assert list(rows[0].keys()) == ["id", "name", "role", "department", "bonus"]
    assert rows[0] == {"id": "1", "name": "Alice", "role": "engineer", "department": "", "bonus": ""}
    assert rows[1] == {"id": "2", "name": "Bob", "role": "", "department": "DeFi", "bonus": ""}
    assert rows[2] == {"id": "3", "name": "", "role": "auditor", "department": "", "bonus": "50"}


def test_invalid_root_type_raises():
    with pytest.raises(ValueError, match="JSON array"):
        json_objects_to_csv_string({"not": "a list"})  # type: ignore[arg-type]
