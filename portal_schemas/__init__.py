"""
AquaGuard Portal Schemas package.
"""

from .compliance import (
    AerationAction,
    PumpAction,
    ValveAction,
    WaterSensorReading,
    WaterAnalysisResult,
    WaterOptimizationPlan,
    ComplianceRecord,
)

__all__ = [
    "AerationAction",
    "PumpAction",
    "ValveAction",
    "WaterSensorReading",
    "WaterAnalysisResult",
    "WaterOptimizationPlan",
    "ComplianceRecord",
]
