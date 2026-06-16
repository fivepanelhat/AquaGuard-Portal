"""
portal_core/ai_agent.py - Upgraded with new SecurityGuard class + enhanced TelemetryTracker

Replaces legacy input_guard_check with the richer SecurityGuard for better auditability.
"""

import asyncio
import json
import logging
import re
from typing import Optional
from datetime import datetime

from coastal_alpine_core.security import SecurityGuard, SecurityResult
from coastal_alpine_core.telemetry import TelemetryTracker
from coastal_alpine_core.models import SovereignOllamaClient

# ... rest of imports and schemas ...

logger = logging.getLogger(__name__)
security_guard = SecurityGuard()  # New richer guard

class AIAgent:
    def __init__(self, ollama_host: str = "http://localhost:11434", model: str = "gemma4:e4b"):
        self.client = SovereignOllamaClient(host=ollama_host, default_model=model)

    async def analyze_sensor_state(self, sensor_data: dict, historical_context: Optional[list] = None) -> dict:
        data_str = f"Sensors: {sensor_data}, History: {historical_context}"

        # === Upgraded SecurityGuard ===
        sec_result: SecurityResult = security_guard.check_prompt(data_str)
        if not sec_result.is_safe:
            logger.warning(f"Blocked by SecurityGuard: {sec_result.reason} (pattern: {sec_result.matched_pattern})")
            return self._generate_default_analysis("Security block")

        measurement = TelemetryTracker.measure_latency("analyze_sensor_state")

        # ... existing prompt construction and inference ...
        # After successful inference:
        TelemetryTracker.complete_measurement(measurement, include_system_metrics=True)
        return parsed_json

    # Similar upgrade applied to generate_optimization_plan and other methods
    # (SecurityGuard + enhanced TelemetryTracker with system metrics)
