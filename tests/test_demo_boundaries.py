"""Boundary tests for the optional, nonclinical demonstration service."""
import math

import pytest
from pydantic import ValidationError

from agents.base import SecurityException
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from simulator import run_simulation


@pytest.mark.parametrize("field,value", [
    ("primary_metric", float("nan")),
    ("primary_metric", float("inf")),
    ("primary_metric", -float("inf")),
    ("secondary_metric", float("nan")),
    ("secondary_metric", float("inf")),
])
def test_demo_rejects_nonfinite_metrics(field, value):
    payload = {
        "task_id": "TEST-01", "target_identifier": "SPECIMEN-01",
        "primary_metric": 1.0,
    }
    payload[field] = value
    with pytest.raises(ValidationError):
        SystemTaskPayload(**payload)


def test_demo_rejects_oversized_identifiers():
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="x" * 129, target_identifier="TEST", primary_metric=1.0)


def test_identifier_guard_includes_attributes():
    payload = SystemTaskPayload(
        task_id="TEST-01", target_identifier="SPECIMEN-01",
        primary_metric=1.0, attributes={"contact": "patient@example.org"},
    )
    with pytest.raises(SecurityException):
        SystemSupervisor().process_task(payload)


@pytest.mark.parametrize("iterations", [0, -1])
def test_simulator_rejects_nonpositive_iterations(iterations):
    with pytest.raises(ValueError, match="positive"):
        run_simulation(iterations)
