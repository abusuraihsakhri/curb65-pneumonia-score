"""Regression tests for clinical input validation and incomplete assessments."""
import json

import pytest

from cli import main
from curb65 import evaluate_patient


BASE = {
    "age": "60",
    "confusion": "no",
    "respiratory_rate": "20",
    "systolic_bp": "120",
    "diastolic_bp": "80",
    "urea": "6",
}


@pytest.mark.parametrize("column,bad", [
    ("confusion", "unknown"),
    ("confusion", "tru"),
    ("urea_elevated", "nope"),
    ("respiratory_rate_high", "maybe"),
    ("blood_pressure_low", "?"),
])
def test_unrecognized_boolean_is_not_silently_normal(column, bad):
    with pytest.raises(ValueError, match="Invalid boolean input"):
        evaluate_patient({**BASE, column: bad})


@pytest.mark.parametrize("column,value", [
    ("respiratory_rate", "0"),
    ("respiratory_rate", "-4"),
    ("respiratory_rate", "nan"),
    ("systolic_bp", "0"),
    ("diastolic_bp", "-3"),
    ("systolic_bp", "infinity"),
])
def test_invalid_csv_vital_signs_rejected(column, value):
    with pytest.raises(ValueError):
        evaluate_patient({**BASE, column: value})


def test_diastolic_above_systolic_rejected():
    with pytest.raises(ValueError, match="Diastolic"):
        evaluate_patient({**BASE, "systolic_bp": "70", "diastolic_bp": "80"})


def test_valid_negative_confusion_flags():
    for negative in ("0", "false", "no", "N", "f"):
        result = evaluate_patient({**BASE, "confusion": negative})
        assert result["curb65_complete"] is True
        assert result["curb65"]["score"] == 0


def test_cli_complete_score(capsys):
    assert main([
        "score", "--age", "40", "--no-confusion", "--rr", "20",
        "--sbp", "120", "--dbp", "80", "--urea", "6", "--json",
    ]) == 0
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["score"] == 0
    assert result["complete"] is True
    assert result["missing_inputs"] == []
    assert captured.err == ""


def test_cli_missing_laboratory_result_is_marked_incomplete(capsys):
    assert main([
        "score", "--age", "40", "--no-confusion", "--rr", "20",
        "--sbp", "120", "--dbp", "80", "--json",
    ]) == 0
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["score"] == 0
    assert result["complete"] is False
    assert "urea_or_bun" in result["missing_inputs"]
    assert "incomplete" in captured.err


def test_cli_missing_confusion_assessment_flagged(capsys):
    assert main([
        "crb65", "--age", "40", "--rr", "20",
        "--sbp", "120", "--dbp", "80", "--json",
    ]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["complete"] is False
    assert "confusion" in result["missing_inputs"]


@pytest.mark.parametrize("flags", [
    ["--age", "-1"],
    ["--age", "nan"],
    ["--age", "121"],
    ["--age", "40", "--rr", "-5"],
    ["--age", "40", "--sbp", "70", "--dbp", "80"],
    ["--age", "40", "--urea", "-1"],
    ["--age", "40", "--bun", "inf"],
    ["--age", "40", "--urea", "6", "--bun", "16"],
])
def test_cli_invalid_measurements_rejected(flags, capsys):
    assert main(["score", *flags, "--json"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Error:" in captured.err
