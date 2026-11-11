#!/usr/bin/env python3
"""
Python 3.10+ JSON-to-CSV Converter
Task ID: cmpupoqmm0027kw04351wcfhz ($50 USDC)
Reads a JSON file (array of flat objects) and converts it to a CSV file,
handling missing keys gracefully by filling them with empty strings ("").
"""

from __future__ import annotations
import argparse
import csv
import io
import json
from pathlib import Path
from typing import Any, Sequence


def json_objects_to_csv_string(
    records: list[dict[str, Any]],
    fieldnames: list[str] | None = None,
    restval: str = "",
) -> str:
    """
    Convert a list of flat JSON objects into an RFC 4180 CSV string.
    Preserves first-seen key order across all objects and fills missing keys or None with `restval` ("").
    """
    if not isinstance(records, list):
        raise ValueError("Input JSON must be a JSON array of objects.")

    for idx, item in enumerate(records):
        if not isinstance(item, dict):
            raise ValueError(f"Element at index {idx} is not a JSON object (dict).")

    if not records:
        return ""

    if fieldnames is None:
        seen: dict[str, None] = {}
        for obj in records:
            for key in obj.keys():
                if key not in seen:
                    seen[key] = None
        fieldnames = list(seen.keys())

    buf = io.StringIO(newline="")
    writer = csv.DictWriter(
        buf,
        fieldnames=fieldnames,
        restval=restval,
        extrasaction="ignore",
        lineterminator="\n",
    )
    writer.writeheader()

    for obj in records:
        normalized_row: dict[str, Any] = {}
        for key in fieldnames:
            val = obj.get(key, restval)
            if val is None:
                normalized_row[key] = restval
            elif isinstance(val, (dict, list)):
                normalized_row[key] = json.dumps(val, ensure_ascii=False)
            else:
                normalized_row[key] = val
        writer.writerow(normalized_row)

    return buf.getvalue()


def convert_json_file_to_csv(
    input_json_path: str | Path,
    output_csv_path: str | Path,
    fieldnames: list[str] | None = None,
) -> int:
    """Read a JSON array file from `input_json_path` and write CSV output to `output_csv_path`."""
    in_path = Path(input_json_path)
    out_path = Path(output_csv_path)
    raw_data = json.loads(in_path.read_text(encoding="utf-8"))
    csv_text = json_objects_to_csv_string(raw_data, fieldnames=fieldnames, restval="")
    out_path.write_text(csv_text, encoding="utf-8", newline="")
    return len(raw_data)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert a JSON file (array of flat objects) to CSV.")
    parser.add_argument("input", help="Path to input JSON file")
    parser.add_argument("output", help="Path to output CSV file")
    args = parser.parse_args(argv)
    count = convert_json_file_to_csv(args.input, args.output)
    print(f"Converted {count} JSON records -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
