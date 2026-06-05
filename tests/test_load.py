import json
import math

import pytest

from checkit.load import quality_gate, row_params


def test_row_params_converts_nan_to_none_and_serializes_errors():
    row = {"record_id": "r1", "headline": "t", "label_confidence": math.nan,
           "validation_errors": ["not-paired"], "url": None}
    params = row_params(row, enc_key="k")
    assert params["label_confidence"] is None
    assert params["url"] is None
    assert params["validation_errors"] == '["not-paired"]'
    assert params["enc_key"] == "k"
    assert params["author_pseudo_id"] is None


def test_row_params_keeps_real_values():
    row = {"record_id": "r1", "label_confidence": 0.9,
           "validation_errors": [], "author_pseudo_id": "abc123"}
    params = row_params(row, enc_key="k")
    assert params["label_confidence"] == 0.9
    assert params["author_pseudo_id"] == "abc123"


def write_report(tmp_path, valid_rate: float):
    p = tmp_path / "run_report.json"
    p.write_text(json.dumps({"valid_rate": valid_rate}))
    return p


def test_quality_gate_passes_above_threshold(tmp_path):
    assert quality_gate(write_report(tmp_path, 0.97), 0.5) == 0.97


def test_quality_gate_aborts_below_threshold(tmp_path):
    with pytest.raises(ValueError, match="quality gate"):
        quality_gate(write_report(tmp_path, 0.31), 0.5)
