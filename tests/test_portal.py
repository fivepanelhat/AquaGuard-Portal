"""
tests/test_portal.py - Unit tests for AquaGuard Portal.

Tests configuration ranges, schema structures, compliance exporters, and actuator mapping.
"""

import sys
import shutil
import pytest
import json
import csv
from pathlib import Path
from datetime import datetime

# Add portal root to import path
sys.path.insert(0, str(Path(__file__).parent.parent))

from coastal_alpine_core.portal_core.config import load_aquaguard_config, AquaGuardConfig
from coastal_alpine_core.portal_core.compliance_exporter import ComplianceExporter
from portal_schemas.compliance import (
    WaterSensorReading,
    WaterAnalysisResult,
    WaterOptimizationPlan,
    ComplianceRecord,
    AerationAction,
    PumpAction,
    ValveAction,
)


@pytest.fixture
def temp_compliance_dir(tmp_path):
    """Temporary folder for testing compliance logs."""
    d = tmp_path / "compliance"
    d.mkdir()
    yield d
    shutil.rmtree(tmp_path)


def test_config_load():
    """Verify config structures and default ranges."""
    config = load_aquaguard_config()
    assert isinstance(config, AquaGuardConfig)
    assert config.thresholds.ph_min < config.thresholds.ph_max
    assert config.thresholds.do_min > 0
    assert config.thresholds.temp_max > 0


def test_sensor_reading_schema():
    """Verify WaterSensorReading Pydantic validations."""
    reading = WaterSensorReading(
        sensor_id="ph_probe_1",
        sensor_type="pH",
        value=7.45,
        unit="pH",
        timestamp=datetime.now(),
    )
    assert reading.value == 7.45
    assert reading.sensor_id == "ph_probe_1"


def test_analysis_result_schema():
    """Verify WaterAnalysisResult Pydantic validations."""
    res = WaterAnalysisResult(
        analysis_id="an-12345",
        status="healthy",
        ph_trend="stable",
        do_trend="stable",
        temperature_trend="increasing",
        turbidity_trend="stable",
        nitrate_trend="decreasing",
        observations="Looks clear, behaviors are normal.",
        timestamp=datetime.now(),
    )
    assert res.status == "healthy"
    assert res.temperature_trend == "increasing"


def test_optimization_plan_schema():
    """Verify WaterOptimizationPlan parsing and actions."""
    plan = WaterOptimizationPlan(
        plan_id="opt-9988",
        aeration_action=AerationAction.HIGH,
        pump_action=PumpAction.MEDIUM,
        valve_action=ValveAction.CLOSED,
        confidence_score=0.92,
        logistical_notes="Oxygen levels drop, boosting aeration.",
        execution_window_minutes=15,
        requires_human_review=False,
    )
    assert plan.aeration_action == AerationAction.HIGH
    assert plan.pump_action == PumpAction.MEDIUM
    assert plan.valve_action == ValveAction.CLOSED
    assert not plan.requires_human_review


@pytest.mark.asyncio
async def test_compliance_record_export(temp_compliance_dir):
    """Verify ComplianceExporter writes JSON audits and appends to CSV ledgers."""
    exporter = ComplianceExporter(compliance_dir=str(temp_compliance_dir))

    record = ComplianceRecord(
        audit_id="aud-112233",
        timestamp=datetime.now(),
        regional_council="Horizons Regional Council",
        consent_id="CONSENT-2026-TEST",
        status="compliant",
        metrics={
            "pH": 7.2,
            "dissolved_oxygen": 6.5,
            "temperature": 16.0,
            "turbidity": 8.0,
            "nitrate": 1.2,
        },
        actions_taken=["aerator: medium", "pump: low", "valve: closed"],
        operator_notes="Validation test execution loop.",
    )

    success = await exporter.export_record(record)
    assert success

    # Verify JSON file exists
    json_files = list(temp_compliance_dir.glob("*.json"))
    assert len(json_files) == 1
    with open(json_files[0], "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["audit_id"] == "aud-112233"
    assert data["status"] == "compliant"

    # Verify CSV ledger exists and has headers and record row
    csv_files = list(temp_compliance_dir.glob("*.csv"))
    assert len(csv_files) == 1
    assert csv_files[0].name == "compliance_ledger_CONSENT-2026-TEST.csv"

    with open(csv_files[0], "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    assert rows[0]["audit_id"] == "aud-112233"
    assert rows[0]["regional_council"] == "Horizons Regional Council"
    assert float(rows[0]["metric_pH"]) == 7.2
    assert float(rows[0]["metric_DO_mgL"]) == 6.5
    assert (
        rows[0]["actions_executed"]
        == "aerator: medium; pump: low; valve: closed"
    )
