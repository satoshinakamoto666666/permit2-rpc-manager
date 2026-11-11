# Python 3.10+ JSON-to-CSV Converter (`cmpupoqmm0027kw04351wcfhz`)

Reads a JSON file containing an array of flat objects and converts it into an RFC 4180 CSV file, filling missing keys and `null` values gracefully with empty strings (`""`).

## Usage

```bash
python json_to_csv.py input.json output.csv
```

## Running Tests

```bash
pytest test_json_to_csv.py
```
