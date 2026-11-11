import json
import pytest
from csv_to_json_converter import InvalidCSVStructureError, ReusableCSVConverter


def test_pipe_delimiter_and_nested_expansion():
    raw = "id|user.name|user.wallet.chain|active\n101|Satoshi|BASE|true\n102|Hal|SOLANA|false\n"
    conv = ReusableCSVConverter(delimiter="|", nested_dot_keys=True, infer_types=True)
    data = json.loads(conv.convert_text(raw))
    assert len(data) == 2
    assert data[0] == {
        "id": 101,
        "user": {"name": "Satoshi", "wallet": {"chain": "BASE"}},
        "active": True,
    }


def test_output_orientations():
    raw = "sku,price\nA1,10.5\nB2,20.0\n"
    col_data = json.loads(ReusableCSVConverter(orientation="columnar").convert_text(raw))
    assert col_data == {"sku": ["A1", "B2"], "price": [10.5, 20.0]}

    keyed_data = json.loads(ReusableCSVConverter(orientation="keyed", key_column="sku").convert_text(raw))
    assert keyed_data["A1"]["price"] == 10.5

    headerless = json.loads(ReusableCSVConverter(has_header=False).convert_text("x,1\ny,2\n"))
    assert headerless[0] == {"field_0": "x", "field_1": 1}


def test_invalid_csv_error_handling():
    conv = ReusableCSVConverter(strict_columns=True)
    with pytest.raises(InvalidCSVStructureError, match="unclosed quote"):
        conv.convert_text('a,b\n1,"unclosed string\n')

    with pytest.raises(InvalidCSVStructureError, match="expected 3 columns"):
        conv.convert_text("a,b,c\n1,2\n")
