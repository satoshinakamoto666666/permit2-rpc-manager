import json
from pathlib import Path
from csv_to_json_parser import csv_to_json, parse_csv_text_to_records


def test_standard_and_special_characters():
    raw_csv = (
        '\ufeffid,name,notes,quote_test\r\n'
        '1,"Alice ""The Coder"" Smith","Line 1\nLine 2\tTabbed","He said, ""Hello!"""\r\n'
        '2,"Bob, Jr.","Unicode: 🚀 € ¥ \\back\\slash","normal"\r\n'
    )
    out = csv_to_json(raw_csv, delimiter=",", infer_types=True)
    parsed = json.loads(out)
    assert len(parsed) == 2
    assert parsed[0]["id"] == 1
    assert parsed[0]["name"] == 'Alice "The Coder" Smith'
    assert parsed[0]["notes"] == "Line 1\nLine 2\tTabbed"
    assert parsed[0]["quote_test"] == 'He said, "Hello!"'
    assert parsed[1]["name"] == "Bob, Jr."
    assert "🚀" in parsed[1]["notes"]
    assert "\\back\\slash" in parsed[1]["notes"]


def test_semicolon_and_tab_auto_detection(tmp_path: Path):
    semi_file = tmp_path / "data.csv"
    semi_file.write_text("symbol;chain;amount\nUSDC;BASE;500.25\nSOL;SOLANA;10\n", encoding="utf-8")
    out = json.loads(csv_to_json(semi_file, infer_types=True))
    assert len(out) == 2
    assert out[0] == {"symbol": "USDC", "chain": "BASE", "amount": 500.25}
    assert out[1] == {"symbol": "SOL", "chain": "SOLANA", "amount": 10}


def test_empty_and_missing_cells():
    records = parse_csv_text_to_records("a,b,c\n1,,3\n\n4,5\n")
    assert len(records) == 2
    assert records[0] == {"a": "1", "b": "", "c": "3"}
    assert records[1] == {"a": "4", "b": "5", "c": ""}
