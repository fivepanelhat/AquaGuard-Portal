"""
main.py - AquaGuard Portal Orchestrator Entrypoint.

Sets up background workers, subscribes to MQTT streams, ingests visual/audio sensors,
routes telemetry through the Gemma 4 reasoning agent, actuates pins, and dumps compliance reports.
"""

import asyncio
import logging
import signal
import uuid
from datetime import datetime
from portal_core.config import load_config, print_config
from portal_core.ai_agent import AIAgent
from portal_core.mqtt_client import MQTTClient
from portal_core.av_capture import AVCapture
from portal_core.hardware_control import HardwareControl
from portal_core.media_pruner import MediaPruner
from portal_core.compliance_exporter import ComplianceExporter
from portal_schemas.compliance import ComplianceRecord

# Config logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("AquaGuardPortal.Orchestrator")


class AquaGuardPortal:
    """
    Main execution coordinator for the AquaGuard edge system.
    """

    def __init__(self, config):
        self.config = config

        self.ai_agent = AIAgent(
            ollama_host=config.ollama.host, model=config.ollama.model
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
        self.hardware_control = HardwareControl(
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

        # Buffer for latest metrics
        self.latest_metrics = {
            "pH": 7.0,
            "dissolved_oxygen": 7.5,
            "temperature": 18.0,
            "turbidity": 5.0,
            "nitrate": 1.0,
        }

        self.is_running = False
        logger.info("AquaGuard Portal system components initialized.")

    async def start(self):
        logger.info("Powering up AquaGuard Portal services...")
        self.is_running = True

        # Initialise hardware GPIO configuration
        await self.hardware_control.setup()

        # Connect to MQTT Broker
        mqtt_connected = await self.mqtt_client.connect()
        if not mqtt_connected:
            logger.warning(
                "Could not establish initial MQTT connection. Ingestion will await re-connection."
            )

        # Setup AV capture streams
        await self.av_capture.start_video_stream()
        await self.av_capture.start_audio_stream()

        # Verify subsystem health status
        health_status = await self.health_check()
        logger.info(f"Subsystem Health Review: {health_status}")

        # Start background workers
        self.pruner_task = asyncio.create_task(self.media_pruner.start())
        self.mqtt_task = asyncio.create_task(self.mqtt_listener_loop())
        self.evaluation_task = asyncio.create_task(
            self.evaluation_control_loop()
        )

        logger.info("✓ AquaGuard Portal is ONLINE and executing.")

        try:
            await asyncio.gather(
                self.pruner_task, self.mqtt_task, self.evaluation_task
            )
        except asyncio.CancelledError:
            logger.info("Subsystem loops cancelled.")

    async def stop(self):
        logger.info("Initiating graceful teardown of AquaGuard Portal...")
        self.is_running = False

        # Terminate background tasks
        if hasattr(self, "pruner_task"):
            self.pruner_task.cancel()
        if hasattr(self, "mqtt_task"):
            self.mqtt_task.cancel()
        if hasattr(self, "evaluation_task"):
            self.evaluation_task.cancel()

        # Shutdown interfaces
        await self.media_pruner.stop()
        await self.av_capture.stop()
        await self.mqtt_client.disconnect()
        await self.hardware_control.cleanup()

        logger.info("✓ AquaGuard Portal shutdown complete.")

    async def health_check(self) -> dict:
        health = {
            "ollama_agent": await self.ai_agent.health_check(),
            "mqtt_broker": await self.mqtt_client.health_check(),
            "av_sensors": await self.av_capture.health_check(),
            "actuator_hardware": await self.hardware_control.health_check(),
            "timestamp": datetime.now().isoformat(),
        }
        return health

    async def mqtt_listener_loop(self):
        """Processes raw incoming MQTT payloads and updates parameter buffers."""
        while self.is_running:
            try:
                msg = await self.mqtt_client.read_message()
                topic = msg.get("topic", "")
                payload = msg.get("payload", {})

                # Payload examples: {"sensor_id": "ph_1", "sensor_type": "pH", "value": 7.4}
                sensor_type = payload.get("sensor_type", "").lower()
                value = payload.get("value")

                if sensor_type and value is not None:
                    # Map to the latest metrics buffer
                    if "ph" in sensor_type:
                        self.latest_metrics["pH"] = float(value)
                    elif "do" in sensor_type or "oxygen" in sensor_type:
                        self.latest_metrics["dissolved_oxygen"] = float(value)
                    elif "temp" in sensor_type or "temperature" in sensor_type:
                        self.latest_metrics["temperature"] = float(value)
                    elif "turbidity" in sensor_type:
                        self.latest_metrics["turbidity"] = float(value)
                    elif "nitrate" in sensor_type:
                        self.latest_metrics["nitrate"] = float(value)

                    logger.debug(f"Updated parameters: {self.latest_metrics}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error handling MQTT listener event: {e}")
                await asyncio.sleep(1)

    async def evaluation_control_loop(self):
        """
        Runs periodic checks (every 15s) compiling sensor readings, executing local SLM reasoning,
        applying physical actuations, and writing regional council compliance audits.
        """
        while self.is_running:
            try:
                # Run evaluation every 15 seconds (reduced for edge workloads)
                await asyncio.sleep(15)
                logger.info(
                    f"Running periodic environmental evaluation check: {self.latest_metrics}"
                )

                # 1. Run local LLM sensor review
                sensor_analysis = await self.ai_agent.analyze_sensor_state(
                    self.latest_metrics
                )

                # 2. Extract visual/acoustic states in parallel
                frame, audio = await asyncio.gather(
                    self.av_capture.capture_frame(),
                    self.av_capture.capture_audio_chunk(),
                )

                visual_analysis, audio_analysis = await asyncio.gather(
                    self.ai_agent.process_visual_feedback(frame),
                    self.ai_agent.process_audio_feedback(audio),
                )

                # 3. Generate hardware optimization commands
                plan = await self.ai_agent.generate_optimization_plan(
                    sensor_analysis, visual_analysis, audio_analysis
                )

                # 4. Apply commands to pins
                enforcement_ok = await self.hardware_control.enforce_plan(plan)
                if enforcement_ok:
                    logger.info(
                        "Enforced optimization plan actions successfully."
                    )
                else:
                    logger.error("Plan actions enforcement failed.")

                # 5. Evaluate breaches to assign regulatory compliance status
                compliance_status = self._evaluate_compliance_status(
                    self.latest_metrics
                )

                # Compile action string
                actions_list = [
                    f"aerator: {plan.get('aeration_action', 'off')}",
                    f"pump: {plan.get('pump_action', 'off')}",
                    f"valve: {plan.get('valve_action', 'closed')}",
                ]

                # 6. Save Compliance Record
                record = ComplianceRecord(
                    audit_id=f"aud-{uuid.uuid4().hex[:8]}",
                    timestamp=datetime.now(),
                    regional_council=self.config.consent.regional_council,
                    consent_id=self.config.consent.consent_id,
                    status=compliance_status,
                    metrics=self.latest_metrics,
                    actions_taken=actions_list,
                    operator_notes=plan.get(
                        "logistical_notes",
                        "Continuous edge telemetry analysis completed successfully.",
                    ),
                )

                await self.compliance_exporter.export_record(record)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    f"Error in evaluation execution loop: {e}", exc_info=True
                )

    def _evaluate_compliance_status(self, metrics: dict) -> str:
        """
        Compares metrics directly with config thresholds to return compliant/breach states.
        """
        limits = self.config.thresholds

        ph = metrics.get("pH", 7.0)
        do = metrics.get("dissolved_oxygen", 6.0)
        temp = metrics.get("temperature", 15.0)
        turb = metrics.get("turbidity", 10.0)
        nitrate = metrics.get("nitrate", 1.0)

        # Check bounds
        if not (limits.ph_min <= ph <= limits.ph_max):
            logger.warning(f"pH limit breached: {ph}")
            return "breach_critical"
        if do < limits.do_min:
            logger.warning(
                f"Dissolved oxygen critical limit breached: {do} (min {limits.do_min})"
            )
            return "breach_critical"
        if temp > limits.temp_max:
            logger.warning(f"Temperature limit breached: {temp}")
            return "breach_warning"
        if turb > limits.turbidity_max:
            logger.warning(f"Turbidity limit breached: {turb}")
            return "breach_warning"
        if nitrate > limits.nitrate_max:
            logger.warning(f"Nitrate limit breached: {nitrate}")
            return "breach_critical"

        return "compliant"


async def main():
    try:
        config = load_config()
        print_config(config)
    except Exception as e:
        logger.error(f"Failed loading initial settings configurations: {e}")
        return

    portal = AquaGuardPortal(config)

    # Register OS signals
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(
                sig, lambda: asyncio.create_task(portal.stop())
            )
        except NotImplementedError:
            # Signal handlers not fully supported on some Windows platforms
            pass

    try:
        await portal.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received.")
        await portal.stop()


if __name__ == "__main__":
    asyncio.run(main())
