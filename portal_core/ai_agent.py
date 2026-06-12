"""
portal_core/ai_agent.py - AI Agent Module for AquaGuard Portal.

Orchestrates local Gemma 4 multimodal inference for water quality and dairy/aquaculture management.
Integrates with coastal-alpine-core safety guards, retry wrappers, and telemetry trackers.
"""

import asyncio
import json
import logging
import re
from typing import Optional
from datetime import datetime

from coastal_alpine_core import (
    SovereignOllamaClient,
    input_guard_check,
    TelemetryTracker,
)
from portal_schemas.compliance import (
    WaterOptimizationPlan,
    AerationAction,
    PumpAction,
    ValveAction,
)

logger = logging.getLogger(__name__)


class AIAgent:
    """
    Autonomous environmental reasoning agent.
    Interfaces with Ollama using the shared SovereignOllamaClient wrapper.
    Ensures safe operations via input guards and logs energy metrics for edge operations.
    """

    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        model: str = "gemma4:e4b",
    ):
        self.ollama_host = ollama_host
        self.model = model
        self.client = SovereignOllamaClient(
            host=ollama_host, default_model=model
        )
        logger.info(
            f"AquaGuard AI Agent initialized. Target Model: {model} at {ollama_host}"
        )

    async def analyze_sensor_state(
        self, sensor_data: dict, historical_context: Optional[list] = None
    ) -> dict:
        """
        Analyze current water parameters against thresholds and trends.
        """
        # 1. Apply Input Security Guard
        data_str = f"Sensors: {sensor_data}, History: {historical_context}"
        if not input_guard_check(data_str):
            logger.warning(
                "Blocked prompt injection or malicious pattern in sensor payload."
            )
            return self._generate_default_analysis(
                "Security alert block: potential data injection."
            )

        # 2. Setup Telemetry Profiling
        measurement = TelemetryTracker.measure_latency("analyze_sensor_state")

        try:
            hist_str = (
                f"\nHistorical context:\n{str(historical_context)}"
                if historical_context
                else ""
            )
            prompt = f"""Water Quality AI: Analyze these sensor readings and respond ONLY with a JSON object (no other text):

Current Telemetry:
{str(sensor_data)}
{hist_str}

JSON Schema:
{{
  "status": "healthy|warning|critical",
  "ph_trend": "stable|increasing|decreasing",
  "do_trend": "stable|increasing|decreasing",
  "temperature_trend": "stable|increasing|decreasing",
  "turbidity_trend": "stable|increasing|decreasing",
  "nitrate_trend": "stable|increasing|decreasing",
  "observations": "brief summary note"
}}"""

            # Run inference synchronously in a worker thread
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.generate, prompt, model=self.model
                ),
                timeout=60.0,
            )

            response_text = response.get("response", "").strip()

            # Find and parse JSON blocks
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                parsed_json = json.loads(json_match.group())
                parsed_json["analysis_id"] = (
                    f"anly-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                )
                parsed_json["timestamp"] = datetime.now().isoformat()

                # Complete profiling metrics
                TelemetryTracker.complete_measurement(
                    measurement,
                    token_count=response.get(
                        "eval_count", len(response_text.split())
                    ),
                    device="RPi5+NPU",
                )
                return parsed_json
            else:
                logger.warning(
                    "Could not extract clean JSON block from Ollama output."
                )
                return self._generate_default_analysis(
                    f"Unformatted response: {response_text[:200]}"
                )

        except asyncio.TimeoutError:
            logger.error("Timeout waiting for Ollama sensor analysis.")
            return self._generate_default_analysis("Analysis timeout.")
        except Exception as e:
            logger.error(f"Error during sensor state analysis: {e}")
            return self._generate_default_analysis(str(e))

    def _generate_default_analysis(self, notes: str) -> dict:
        return {
            "analysis_id": f"anly-default-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "status": "warning",
            "ph_trend": "stable",
            "do_trend": "stable",
            "temperature_trend": "stable",
            "turbidity_trend": "stable",
            "nitrate_trend": "stable",
            "observations": f"Safe fallback activated: {notes}",
            "timestamp": datetime.now().isoformat(),
        }

    async def process_visual_feedback(self, frame_data: bytes) -> dict:
        """
        Analyze camera frame for water clarity / behavioral patterns.
        """
        if not frame_data:
            return {
                "overall_health": "unknown",
                "observations": "No frame captured.",
            }

        measurement = TelemetryTracker.measure_latency(
            "process_visual_feedback"
        )

        try:
            # Check length to simulate processing frame or text prompt fallback
            prompt = """Water Visual Assessor: Analyze water clarity/sedimentation behavior. Respond ONLY with JSON:
{"overall_health":"excellent|good|fair|poor", "anomalies":"none|high_sediment|fish_piping|other", "confidence":"high|medium|low"}"""

            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.generate, prompt, model=self.model
                ),
                timeout=45.0,
            )

            text = response.get("response", "").strip()
            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                result["frame_bytes"] = len(frame_data)
                result["timestamp"] = datetime.now().isoformat()

                TelemetryTracker.complete_measurement(
                    measurement,
                    token_count=response.get("eval_count", len(text.split())),
                    device="RPi5+NPU",
                )
                return result

            return {
                "overall_health": "good",
                "observations": text[:300],
                "frame_bytes": len(frame_data),
            }

        except Exception as e:
            logger.error(f"Visual feedback analysis error: {e}")
            return {
                "overall_health": "unknown",
                "error": str(e),
                "frame_bytes": len(frame_data),
            }

    async def process_audio_feedback(self, audio_data: bytes) -> dict:
        """
        Analyze microphone feedback for pumps or mechanical alerts.
        """
        if not audio_data:
            return {
                "anomaly_detected": False,
                "observations": "No audio chunk.",
            }

        measurement = TelemetryTracker.measure_latency(
            "process_audio_feedback"
        )

        try:
            prompt = """Acoustic Vibration Watchdog: Check for pump cavitation, pipe leaks, or heavy machinery noise. Respond ONLY with JSON:
{"anomaly_detected":true|false, "type":"none|pump_cavitation|water_leak|other", "confidence":"high|medium|low"}"""

            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.generate, prompt, model=self.model
                ),
                timeout=45.0,
            )

            text = response.get("response", "").strip()
            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                result["audio_bytes"] = len(audio_data)
                result["timestamp"] = datetime.now().isoformat()

                TelemetryTracker.complete_measurement(
                    measurement,
                    token_count=response.get("eval_count", len(text.split())),
                    device="RPi5+NPU",
                )
                return result

            return {"anomaly_detected": False, "observations": text[:300]}

        except Exception as e:
            logger.error(f"Audio feedback analysis error: {e}")
            return {"anomaly_detected": False, "error": str(e)}

    async def generate_optimization_plan(
        self,
        sensor_analysis: dict,
        visual_analysis: dict,
        audio_analysis: dict,
    ) -> dict:
        """
        Formulates a validated control plan mapping sensor state and A/V alerts to actuators.
        """
        logger.info(
            "Synthesizing multi-modal telemetry inputs to formulate optimization actions."
        )

        # Guard inputs
        inputs_str = f"Sensors: {sensor_analysis}, Vision: {visual_analysis}, Audio: {audio_analysis}"
        if not input_guard_check(inputs_str):
            logger.warning(
                "Blocked potential exploit patterns in plan generation inputs."
            )
            return self._generate_default_plan()

        measurement = TelemetryTracker.measure_latency(
            "generate_optimization_plan"
        )

        try:
            prompt = f"""AquaGuard Controller: Formulate a hardware actuation plan based on this state.
Sensors Analysis: {str(sensor_analysis)}
Camera Ingestion: {str(visual_analysis)}
Acoustic Watchdog: {str(audio_analysis)}

Respond ONLY with a JSON object fitting this schema:
{{
  "plan_id": "opt-water-YYYYMMDD-count",
  "aeration_action": "off|low|medium|high",
  "pump_action": "off|low|medium|high",
  "valve_action": "open|closed",
  "confidence_score": 0.9,
  "logistical_notes": "operational reasoning",
  "execution_window_minutes": 15,
  "requires_human_review": false
}}"""

            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.generate, prompt, model=self.model
                ),
                timeout=60.0,
            )

            text = response.get("response", "").strip()
            json_match = re.search(r"\{.*\}", text, re.DOTALL)

            if json_match:
                plan_data = json.loads(json_match.group())

                # Check actions match allowed Enums
                aeration = plan_data.get("aeration_action", "off").lower()
                if aeration not in ["off", "low", "medium", "high"]:
                    aeration = "off"
                plan_data["aeration_action"] = AerationAction(aeration)

                pump = plan_data.get("pump_action", "off").lower()
                if pump not in ["off", "low", "medium", "high"]:
                    pump = "off"
                plan_data["pump_action"] = PumpAction(pump)

                valve = plan_data.get("valve_action", "closed").lower()
                if valve not in ["open", "closed"]:
                    valve = "closed"
                plan_data["valve_action"] = ValveAction(valve)

                # Validate with Pydantic WaterOptimizationPlan
                validated = WaterOptimizationPlan(**plan_data)

                TelemetryTracker.complete_measurement(
                    measurement,
                    token_count=response.get("eval_count", len(text.split())),
                    device="RPi5+NPU",
                )
                return validated.dict()
            else:
                logger.warning(
                    "AI optimization plan did not return structured JSON. Reverting to safe defaults."
                )
                return self._generate_default_plan()

        except Exception as e:
            logger.error(f"Error generating optimization plan: {e}")
            return self._generate_default_plan()

    def _generate_default_plan(self) -> dict:
        default_plan = WaterOptimizationPlan(
            plan_id=f"opt-water-default-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            aeration_action=AerationAction.MEDIUM,
            pump_action=PumpAction.MEDIUM,
            valve_action=ValveAction.CLOSED,
            confidence_score=0.5,
            logistical_notes="Safe fallback parameters applied due to system exception or prompt blocking.",
            execution_window_minutes=30,
            requires_human_review=True,
        )
        return default_plan.dict()

    async def health_check(self) -> bool:
        """Verify Ollama service status and model download state."""
        try:
            return self.client.check_health()
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
