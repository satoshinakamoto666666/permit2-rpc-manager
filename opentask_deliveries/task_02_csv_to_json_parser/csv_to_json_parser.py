#!/usr/bin/env python3
"""
Production-Grade Python CSV-to-JSON Parser
Task ID: cmp545xcw001bl704p3a7ock7 ($100 USDC)
Handles RFC 4180 CSV dialects, UTF-8 / UTF-8-SIG BOM, embedded multiline strings,
escaped quotes, Unicode/control character JSON escaping, and automatic dialect detection.
"""

from __future__ import annotations
import argparse
import csv
import io
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union


def infer_scalar(val: Optional[str], infer_types: bool = False) -> Any:
    """Convert raw CSV string cell to typed scalar when infer_types=True."""
    if val is None:
        return None
    if not infer_types:
        return val
    stripped = val.strip()
    if stripped == "":
        return ""
    low = stripped.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low in ("null", "none"):
        return None
    try:
        if stripped.isdigit() or (stripped.startswith("-") and stripped[1:].isdigit()):
            return int(stripped)
        return float(stripped)
    except ValueError:
        return val


def parse_csv_text_to_records(
    csv_text: str,
    delimiter: Optional[str] = None,
    quotechar: str = '"',
    infer_types: bool = False,
    skip_blank_lines: bool = True,
) -> List[Dict[str, Any]]:
    """
    Parse CSV text into a list of dictionary records with automatic dialect sniffing
    and full RFC 4180 special-character handling.
    """
    if csv_text.startswith("\ufeff"):
        csv_text = csv_text.lstrip("\ufeff")

    if not csv_text.strip():
        return []

    sample = csv_text[:4096]
    dialect: Any = csv.excel
    if delimiter is None:
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
        except csv.Error:
            dialect = csv.excel
    else:
        class CustomDialect(csv.excel):
            pass
        CustomDialect.delimiter = delimiter
        CustomDialect.quotechar = quotechar
        dialect = CustomDialect

    stream = io.StringIO(csv_text, newline="")
    reader = csv.reader(stream, dialect=dialect)

    try:
        raw_headers = next(reader)
    except StopIteration:
        return []

    headers = [h.strip() if h is not None else f"col_{idx}" for idx, h in enumerate(raw_headers)]
    records: List[Dict[str, Any]] = []

    for row in reader:
        if skip_blank_lines and (not row or all(cell.strip() == "" for cell in row)):
            continue
        record: Dict[str, Any] = {}
        for idx, header in enumerate(headers):
            raw_val = row[idx] if idx < len(row) else ""
            record[header] = infer_scalar(raw_val, infer_types=infer_types)
        if len(row) > len(headers):
            record["_extra"] = [infer_scalar(c, infer_types=infer_types) for c in row[len(headers):]]
        records.append(record)

    return records


def csv_to_json(
    source: Union[str, Path, io.TextIOBase],
    delimiter: Optional[str] = None,
    infer_types: bool = False,
    indent: Optional[int] = 2,
    ensure_ascii: bool = False,
) -> str:
    """Read CSV from file path, stream, or raw text and output formatted JSON string."""
    if isinstance(source, Path):
        text = source.read_text(encoding="utf-8-sig")
    elif hasattr(source, "read"):
        text = source.read()
    else:
        p = Path(str(source))
        if p.exists() and p.is_file():
            text = p.read_text(encoding="utf-8-sig")
        else:
            text = str(source)

    records = parse_csv_text_to_records(text, delimiter=delimiter, infer_types=infer_types)
    return json.dumps(records, indent=indent, ensure_ascii=ensure_ascii)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Parse CSV files and generate JSON output.")
    parser.add_argument("input", help="Input CSV file path")
    parser.add_argument("-o", "--output", help="Output JSON file path (defaults to stdout)")
    parser.add_argument("-d", "--delimiter", help="Explicit CSV delimiter (auto-detected if omitted)")
    parser.add_argument("--infer-types", action="store_true", help="Infer numbers, booleans, and nulls")
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation spaces (default: 2)")
    parser.add_argument("--ascii", action="store_true", help="Escape non-ASCII characters in JSON output")
    args = parser.parse_args(argv)

    json_out = csv_to_json(
        Path(args.input),
        delimiter=args.delimiter,
        infer_types=args.infer_types,
        indent=args.indent,
        ensure_ascii=args.ascii,
    )
    if args.output:
        Path(args.output).write_text(json_out + "\n", encoding="utf-8")
    else:
        print(json_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
