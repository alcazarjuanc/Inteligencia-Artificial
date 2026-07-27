"""Tests for pipeline.py."""

import csv
import os
import tempfile

from pipeline import load_csv, validate_schema, remove_duplicates
from pipeline import handle_missing_numeric, numeric_summary


def _write_csv(rows, header=None):
    """Helper: write rows to a temp CSV and return the path."""
    f, path = tempfile.mkstemp(suffix=".csv")
    os.close(f)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=header or rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_load_csv():
    path = _write_csv(
        [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}], header=["a", "b"]
    )
    rows = load_csv(path)
    assert rows == [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]
    os.unlink(path)


def test_validate_schema():
    rows = [{"x": 1, "y": 2}, {"x": 3, "y": 4}]
    assert validate_schema(rows, ["x", "y"]) is True
    assert validate_schema(rows, ["x", "z"]) is False


def test_remove_duplicates_complete():
    rows = [{"a": 1}, {"a": 2}, {"a": 1}]
    result = remove_duplicates(rows)
    assert len(result) == 2
    assert result[0]["a"] == 1
    assert result[1]["a"] == 2


def test_remove_duplicates_key():
    rows = [{"a": 1, "b": "x"}, {"a": 1, "b": "y"}, {"a": 2, "b": "x"}]
    result = remove_duplicates(rows, key_columns=["a"])
    assert len(result) == 2
    assert result[0]["b"] == "x"  # first occurrence kept


def test_handle_missing_imputation():
    rows = [{"v": "10"}, {"v": ""}, {"v": "20"}]
    result = handle_missing_numeric(rows, ["v"])
    assert len(result) == 3
    assert result[0]["v"] == 10.0
    assert result[1]["v"] == 15.0  # mean of 10 and 20
    assert result[2]["v"] == 20.0


def test_input_immutability():
    rows = [{"v": "10"}, {"v": None}]
    orig = [{"v": "10"}, {"v": None}]
    handle_missing_numeric(rows, ["v"])
    assert rows == orig  # original not mutated


def test_numeric_summary():
    rows = [{"v": "10"}, {"v": "20"}, {"v": None}]
    summary = numeric_summary(rows, ["v"])
    assert summary["v"]["count"] == 2
    assert summary["v"]["mean"] == 15.0
    assert summary["v"]["min"] == 10.0
    assert summary["v"]["max"] == 20.0


def test_valueerror_no_usable():
    rows = [{"v": None}, {"v": ""}]
    try:
        numeric_summary(rows, ["v"])
        assert False, "Expected ValueError"
    except ValueError:
        pass
