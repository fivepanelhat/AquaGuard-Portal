"""
main.py - AquaGuard Portal with Full Data Flywheel + SessionEvent Integration
"""

import asyncio
import logging
import signal
import uuid
from datetime import datetime

from coastal_alpine_core.portal_core.config import load_aquaguard_config, print_config
from coastal_alpine_core.portal_core.ai_agent import AIAgent
from coastal_alpine_core.portal_core.mqtt_client import MQTTClient
from coastal_alpine_core.portal_core.av_capture import AVCapture
from coastal_alpine_core.portal_core.hardware_control import HardwareController
from coastal_alpine_core.portal_core.media_pruner import MediaPruner
from coastal_alpine_core.portal_core.compliance_exporter import ComplianceExporter
from portal_schemas.compliance import ComplianceRecord

from coastal_alpine_core import DataFlywheel
from session_bridge import PortalSession, timed

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("AquaGuardPortal.Orchestrator")


class AquaGuardPortal:
    def __init__(self, config):
        self.config = config
        self.flywheel_path = "flywheel_aquaguard.jsonl"
        self.flywheel = DataFlywheel(storage_path=self.flywheel_path)
        self.session = PortalSession("aquaguard")

        self.ai_agent = AIAgent(
            ollama_host=config.ollama.host,
            model=config.ollama.model,
            flywheel=self.flywheel,
        )
        self.mqtt_client = MQTTClient(
            broker_host=config.mqtt.broker,
            broker_port=config.mqtt.port,
            topic_prefix=config.mqtt.topic_prefix,
            username=config.mqtt.username,
            password=config.mqtt.password,
        )
        self.av_capture = AVCapture(
            camera_index=config.camera.device_index,
            video_fps=config.camera.fps,
            audio_sample_rate=config.audio.sample_rate,
            audio_chunk_size=config.audio.chunk_size,
        )
        self.hardware_control = HardwareController(
            aerator_gpio_pin=config.hardware.aerator_gpio_pin,
            pump_gpio_pin=config.hardware.pump_gpio_pin,
            valve_gpio_pin=config.hardware.valve_gpio_pin,
            alert_gpio_pin=config.hardware.alert_gpio_pin,
            enable_hardware_control=config.hardware.enable_hardware_control,
        )
        self.media_pruner = MediaPruner(
            media_dir=str(config.storage.media_dir),
            sensor_logs_dir=str(config.storage.sensor_logs_dir),
            compliance_dir=str(config.storage.compliance_dir),
            retention_hours=config.storage.retention_hours,
            critical_disk_usage_pct=config.storage.critical_disk_usage_pct,
        )
        self.compliance_exporter = ComplianceExporter(
            compliance_dir=str(config.storage.compliance_dir)
        )

        self.latest_metrics = {
            "pH": 7.0, "dissolved_oxygen": 7.5, "temperature": 18.0,
            "turbidity": 5.0, "nitrate": 1.0,
        }
        self.is_running = False
        logger.info("AquaGuard Portal initialized (flywheel + SessionEvent soft bridge).")

    async def evaluation_control_loop(self):
        while self.is_running:
            try:
                await asyncio.sleep(15)
                session_id = self.session.new_session_id()
                t0 = timed()
                self.session.emit(
                    session_id,
                    "prompt_received",
                    actor="aquaguard",
                    payload={"metrics_keys": list(self.latest_metrics.keys())},
                )

                sensor_analysis = await self.ai_agent.analyze_sensor_state(self.latest_metrics)
                frame, audio = await asyncio.gather(
                    self.av_capture.capture_frame(),
                    self.av_capture.capture_audio_chunk(),
                )
                visual_analysis, audio_analysis = await asyncio.gather(
                    self.ai_agent.process_visual_feedback(frame),
                    self.ai_agent.process_audio_feedback(audio),
                )

                plan = await self.ai_agent.generate_optimization_plan(
                    sensor_analysis, visual_analysis, audio_analysis
                )
                self.session.emit(
                    session_id,
                    "agent_step",
                    actor="ai_agent",
                    payload={"has_plan": bool(plan)},
                )

                enforcement_ok = await self.hardware_control.enforce_plan(plan)

                if plan:
                    action = plan.get("aeration_action") or plan.get("pump_action") or plan.get("valve_action") or "unknown"
                    self.ai_agent.record_hardware_result(
                        plan_id=plan.get("plan_id", "unknown"),
                        action=action,
                        success=enforcement_ok,
                        metadata=plan
                    )

                outcome = "success" if enforcement_ok else "error"
                self.session.complete_cycle(
                    session_id,
                    action="aquaguard.plan_cycle",
                    outcome=outcome,
                    latency_seconds=timed() - t0,
                    input_summary=f"metrics={len(self.latest_metrics)}",
                    output_summary=f"enforced={enforcement_ok}",
                    flywheel_path=self.flywheel_path,
                )

                if enforcement_ok:
                    logger.info("Enforced optimization plan actions successfully.")
                else:
                    logger.error("Plan actions enforcement failed.")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in evaluation execution loop: {e}", exc_info=True)
