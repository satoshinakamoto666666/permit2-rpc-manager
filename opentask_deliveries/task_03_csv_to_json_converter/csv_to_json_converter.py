#!/usr/bin/env python3
"""
Reusable Python CSV-to-JSON Converter (Arbitrary Structures, Delimiters, Output Layouts & Validation)
Task ID: cmp545t0n0011l704htzztdbb ($100 USDC)
"""

from __future__ import annotations
import argparse
import csv
import io
import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Sequence, Union


class InvalidCSVStructureError(ValueError):
    """Raised when a CSV input is structurally malformed or fails strict row-width validation."""


OutputOrientation = Literal["records", "columnar", "keyed", "values", "ndjson"]


def expand_nested_keys(flat_record: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
    """Expand dotted column headers (e.g. 'user.name') into nested JSON objects."""
    nested: Dict[str, Any] = {}
    for key, value in flat_record.items():
        parts = key.split(separator) if separator in key else [key]
        target = nested
        for part in parts[:-1]:
            if part not in target or not isinstance(target[part], dict):
                target[part] = {}
            target = target[part]
        target[parts[-1]] = value
    return nested


class ReusableCSVConverter:
    """
    Reusable CSV-to-JSON converter supporting:
    - Arbitrary delimiters (',', ';', '\\t', '|', custom) or auto-detection
    - Headered or headerless CSV files (auto-generates field_0, field_1, ...)
    - Nested object expansion via dot notation ('address.city' -> {'address': {'city': ...}})
    - Multiple JSON output structures: 'records', 'columnar', 'keyed', 'values', 'ndjson'
    - Strict structural validation for unclosed quotes, NUL bytes, and inconsistent column counts
    """

    def __init__(
        self,
        delimiter: Optional[str] = None,
        has_header: bool = True,
        strict_columns: bool = False,
        nested_dot_keys: bool = False,
        infer_types: bool = True,
        orientation: OutputOrientation = "records",
        key_column: Optional[str] = None,
        indent: Optional[int] = 2,
        sort_keys: bool = False,
    ) -> None:
        self.delimiter = delimiter
        self.has_header = has_header
        self.strict_columns = strict_columns
        self.nested_dot_keys = nested_dot_keys
        self.infer_types = infer_types
        self.orientation = orientation
        self.key_column = key_column
        self.indent = indent
        self.sort_keys = sort_keys

    @staticmethod
    def _coerce(val: str, infer: bool) -> Any:
        if not infer:
            return val
        s = val.strip()
        if s == "":
            return ""
        low = s.lower()
        if low == "true":
            return True
        if low == "false":
            return False
        if low in ("null", "none", "na", "n/a"):
            return None
        try:
            if s.isdigit() or (s.startswith("-") and s[1:].isdigit()):
                return int(s)
            return float(s)
        except ValueError:
            return val

    def _validate_raw_text(self, text: str) -> str:
        if "\x00" in text:
            raise InvalidCSVStructureError("Invalid CSV: contains NUL (\\x00) byte.")
        if text.startswith("\ufeff"):
            text = text.lstrip("\ufeff")
        # Check for unclosed quotes in RFC 4180 stream
        in_quotes = False
        i = 0
        n = len(text)
        while i < n:
            ch = text[i]
            if ch == '"':
                if in_quotes and i + 1 < n and text[i + 1] == '"':
                    i += 2
                    continue
                in_quotes = not in_quotes
            i += 1
        if in_quotes:
            raise InvalidCSVStructureError("Invalid CSV: unclosed quote character detected before EOF.")
        return text

    def convert_text(self, raw_text: str) -> str:
        text = self._validate_raw_text(raw_text)
        if not text.strip():
            return "[]" if self.orientation != "ndjson" else ""

        delimiter = self.delimiter
        if delimiter is None:
            try:
                dialect = csv.Sniffer().sniff(text[:4096], delimiters=[",", ";", "\t", "|", ":"])
                delimiter = dialect.delimiter
            except csv.Error:
                delimiter = ","

        stream = io.StringIO(text, newline="")
        reader = csv.reader(stream, delimiter=delimiter, quotechar='"', strict=True)

        try:
            rows = [r for r in reader if any(cell.strip() != "" for cell in r)]
        except csv.Error as exc:
            raise InvalidCSVStructureError(f"Malformed CSV row: {exc}") from exc

        if not rows:
            return "[]" if self.orientation != "ndjson" else ""

        if self.has_header:
            headers = [h.strip() or f"field_{i}" for i, h in enumerate(rows[0])]
            data_rows = rows[1:]
        else:
            max_cols = max(len(r) for r in rows)
            headers = [f"field_{i}" for i in range(max_cols)]
            data_rows = rows

        expected_width = len(headers)
        records: List[Dict[str, Any]] = []

        for line_idx, row in enumerate(data_rows, start=2 if self.has_header else 1):
            if self.strict_columns and len(row) != expected_width:
                raise InvalidCSVStructureError(
                    f"Row {line_idx} has {len(row)} columns, expected {expected_width} columns."
                )
            rec: Dict[str, Any] = {}
            for col_idx, h in enumerate(headers):
                raw_val = row[col_idx] if col_idx < len(row) else ""
                rec[h] = self._coerce(raw_val, self.infer_types)
            if not self.strict_columns and len(row) > expected_width:
                for extra_idx, extra_val in enumerate(row[expected_width:], start=expected_width):
                    rec[f"field_{extra_idx}"] = self._coerce(extra_val, self.infer_types)
            if self.nested_dot_keys:
                rec = expand_nested_keys(rec)
            records.append(rec)

        if self.orientation == "ndjson":
            return "\n".join(json.dumps(r, sort_keys=self.sort_keys, ensure_ascii=False) for r in records)
        if self.orientation == "columnar":
            col_map: Dict[str, List[Any]] = {h: [] for h in headers}
            for r in records:
                for h in headers:
                    col_map[h].append(r.get(h))
            return json.dumps(col_map, indent=self.indent, sort_keys=self.sort_keys, ensure_ascii=False)
        if self.orientation == "keyed":
            key_col = self.key_column or headers[0]
            keyed_map = {str(r.get(key_col, idx)): r for idx, r in enumerate(records)}
            return json.dumps(keyed_map, indent=self.indent, sort_keys=self.sort_keys, ensure_ascii=False)
        if self.orientation == "values":
            matrix = [[self._coerce(c, self.infer_types) for c in r] for r in data_rows]
            return json.dumps(matrix, indent=self.indent, ensure_ascii=False)

        return json.dumps(records, indent=self.indent, sort_keys=self.sort_keys, ensure_ascii=False)

    def convert_file(self, input_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None) -> str:
        p = Path(input_path)
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"CSV file not found: {p}")
        raw_text = p.read_text(encoding="utf-8-sig")
        result = self.convert_text(raw_text)
        if output_path is not None:
            Path(output_path).write_text(result + "\n", encoding="utf-8")
        return result


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Convert CSV files of any structure into formatted JSON.")
    parser.add_argument("input", help="Path to input CSV file")
    parser.add_argument("-o", "--output", help="Path to output JSON file")
    parser.add_argument("-d", "--delimiter", help="Custom CSV delimiter (',', ';', '|', '\\t')")
    parser.add_argument("--no-header", action="store_true", help="Treat CSV as headerless")
    parser.add_argument("--strict", action="store_true", help="Fail if any row has mismatched column count")
    parser.add_argument("--nested", action="store_true", help="Expand dot-separated headers into nested objects")
    parser.add_argument(
        "--format",
        choices=["records", "columnar", "keyed", "values", "ndjson"],
        default="records",
        help="Output JSON structure format",
    )
    parser.add_argument("--key-column", help="Key column name when --format=keyed")
    parser.add_argument("--indent", type=int, default=2, help="Indentation level")
    args = parser.parse_args(argv)

    converter = ReusableCSVConverter(
        delimiter=args.delimiter,
        has_header=not args.no_header,
        strict_columns=args.strict,
        nested_dot_keys=args.nested,
        orientation=args.format,
        key_column=args.key_column,
        indent=args.indent,
    )
    out = converter.convert_file(args.input, args.output)
    if not args.output:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
