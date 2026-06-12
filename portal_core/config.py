"""
portal_core/config.py - Configuration Module for AquaGuard Portal.

Validates and loads environmental settings, sensor thresholds, hardware control maps, and consent metrics.
"""

import os
import logging
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class OllamaConfig(BaseModel):
    """Local Ollama LLM execution parameters."""

    host: str = Field(default="http://localhost:11434")
    model: str = Field(default="gemma4:e4b")

    @validator("host")
    def validate_host(cls, v):
        if not v.startswith("http://") and not v.startswith("https://"):
            raise ValueError("Ollama host must start with http:// or https://")
        return v


class MQTTConfig(BaseModel):
    """MQTT broker connection parameters."""

    broker: str = Field(default="localhost")
    port: int = Field(default=1883, ge=1, le=65535)
    username: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)
    topic_prefix: str = Field(default="aquaguard/sensors")


class StorageConfig(BaseModel):
    """Storage directories and media file pruner thresholds."""

    media_dir: Path = Field(default=Path("./telemetry_data/media"))
    sensor_logs_dir: Path = Field(default=Path("./telemetry_data/sensor_logs"))
    compliance_dir: Path = Field(default=Path("./telemetry_data/compliance"))
    retention_hours: int = Field(default=48, ge=1)
    critical_disk_usage_pct: float = Field(default=85.0, ge=50.0, le=99.0)

    @validator("media_dir", "sensor_logs_dir", "compliance_dir", pre=True)
    def create_and_validate_paths(cls, v):
        path = Path(v) if isinstance(v, str) else v
        path.mkdir(parents=True, exist_ok=True)
        return path


class CameraConfig(BaseModel):
    """Physical CSI/USB camera configurations."""

    device_index: int = Field(default=0, ge=0)
    fps: int = Field(default=30, ge=5, le=120)


class AudioConfig(BaseModel):
    """Audio sampling settings for acoustic leak monitoring."""

    sample_rate: int = Field(default=16000)
    chunk_size: int = Field(default=4096, ge=256, le=65536)

    @validator("sample_rate")
    def validate_rate(cls, v):
        valid = [8000, 16000, 44100, 48000]
        if v not in valid:
            raise ValueError(f"Sample rate must be one of {valid}")
        return v


class HardwareConfig(BaseModel):
    """Raspberry Pi GPIO allocations and control parameters."""

    aerator_gpio_pin: Optional[int] = Field(default=None)
    pump_gpio_pin: Optional[int] = Field(default=None)
    valve_gpio_pin: Optional[int] = Field(default=None)
    alert_gpio_pin: Optional[int] = Field(default=None)
    enable_hardware_control: bool = Field(default=False)


class ConsentConfig(BaseModel):
    """Consent credentials representing the target council."""

    regional_council: str = Field(default="Horizons Regional Council")
    consent_id: str = Field(default="CONSENT-2026-AUTH-0981")


class ThresholdConfig(BaseModel):
    """Operational limits defined by resource consents or guidelines."""

    ph_min: float = Field(default=6.5, ge=0.0, le=14.0)
    ph_max: float = Field(default=8.5, ge=0.0, le=14.0)
    do_min: float = Field(default=5.0, ge=0.0)
    temp_max: float = Field(default=24.0, ge=0.0)
    turbidity_max: float = Field(default=50.0, ge=0.0)
    nitrate_max: float = Field(default=10.0, ge=0.0)


class LoggingConfig(BaseModel):
    """Daemon logging profiles."""

    level: str = Field(default="INFO")
    file: Optional[Path] = Field(default=None)

    @validator("level")
    def validate_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()


class AquaGuardConfig(BaseModel):
    """Comprehensive AquaGuard System configuration model."""

    ollama: OllamaConfig
    mqtt: MQTTConfig
    storage: StorageConfig
    camera: CameraConfig
    audio: AudioConfig
    hardware: HardwareConfig
    consent: ConsentConfig
    thresholds: ThresholdConfig
    logging: LoggingConfig


def load_config() -> AquaGuardConfig:
    """
    Load environment variables from .env and compile validated AquaGuardConfig.
    """
    # Find .env relative to current run or workspace roots
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)
        logger.info(
            f"Loaded configuration from environment file: {env_file.resolve()}"
        )
    else:
        logger.warning(
            "No .env configuration file discovered; utilizing runtime defaults."
        )

    try:
        ollama_cfg = OllamaConfig(
            host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "gemma4:e4b"),
        )

        mqtt_cfg = MQTTConfig(
            broker=os.getenv("MQTT_BROKER", "localhost"),
            port=int(os.getenv("MQTT_PORT", "1883")),
            username=os.getenv("MQTT_USERNAME"),
            password=os.getenv("MQTT_PASSWORD"),
            topic_prefix=os.getenv("MQTT_TOPIC_PREFIX", "aquaguard/sensors"),
        )

        storage_cfg = StorageConfig(
            media_dir=os.getenv("MEDIA_DIR", "./telemetry_data/media"),
            sensor_logs_dir=os.getenv(
                "SENSOR_LOGS_DIR", "./telemetry_data/sensor_logs"
            ),
            compliance_dir=os.getenv(
                "COMPLIANCE_DIR", "./telemetry_data/compliance"
            ),
            retention_hours=int(os.getenv("MEDIA_RETENTION_HOURS", "48")),
            critical_disk_usage_pct=float(
                os.getenv("CRITICAL_DISK_USAGE_PCT", "85.0")
            ),
        )

        camera_cfg = CameraConfig(
            device_index=int(os.getenv("CAMERA_DEVICE_INDEX", "0")),
            fps=int(os.getenv("CAMERA_FPS", "30")),
        )

        audio_cfg = AudioConfig(
            sample_rate=int(os.getenv("AUDIO_SAMPLE_RATE", "16000")),
            chunk_size=int(os.getenv("AUDIO_CHUNK_SIZE", "4096")),
        )

        hw_cfg = HardwareConfig(
            aerator_gpio_pin=(
                int(p)
                if (p := os.getenv("HARDWARE_AERATOR_GPIO_PIN"))
                else None
            ),
            pump_gpio_pin=(
                int(p) if (p := os.getenv("HARDWARE_PUMP_GPIO_PIN")) else None
            ),
            valve_gpio_pin=(
                int(p) if (p := os.getenv("HARDWARE_VALVE_GPIO_PIN")) else None
            ),
            alert_gpio_pin=(
                int(p) if (p := os.getenv("HARDWARE_ALERT_GPIO_PIN")) else None
            ),
            enable_hardware_control=os.getenv(
                "HARDWARE_ENABLE_CONTROL", "false"
            ).lower()
            == "true",
        )

        consent_cfg = ConsentConfig(
            regional_council=os.getenv(
                "REGIONAL_COUNCIL", "Horizons Regional Council"
            ),
            consent_id=os.getenv("CONSENT_ID", "CONSENT-2026-AUTH-0981"),
        )

        thresholds_cfg = ThresholdConfig(
            ph_min=float(os.getenv("THRESHOLD_PH_MIN", "6.5")),
            ph_max=float(os.getenv("THRESHOLD_PH_MAX", "8.5")),
            do_min=float(os.getenv("THRESHOLD_DO_MIN", "5.0")),
            temp_max=float(os.getenv("THRESHOLD_TEMP_MAX", "24.0")),
            turbidity_max=float(os.getenv("THRESHOLD_TURBIDITY_MAX", "50.0")),
            nitrate_max=float(os.getenv("THRESHOLD_NITRATE_MAX", "10.0")),
        )

        logging_cfg = LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            file=Path(f) if (f := os.getenv("LOG_FILE")) else None,
        )

        config = AquaGuardConfig(
            ollama=ollama_cfg,
            mqtt=mqtt_cfg,
            storage=storage_cfg,
            camera=camera_cfg,
            audio=audio_cfg,
            hardware=hw_cfg,
            consent=consent_cfg,
            thresholds=thresholds_cfg,
            logging=logging_cfg,
        )

        logger.info("✓ Configurations loaded and validated successfully.")
        return config

    except Exception as e:
        logger.error(
            f"✗ Failed loading / validating configuration parameters: {e}"
        )
        raise


def print_config(config: AquaGuardConfig):
    """
    Format and dump configuration state for visual validation during boot.
    """
    logger.info("=" * 60)
    logger.info("AquaGuard Portal Operational Parameters")
    logger.info("=" * 60)
    logger.info(
        f"Ollama Target   : {config.ollama.host} (model: {config.ollama.model})"
    )
    logger.info(
        f"MQTT Target     : {config.mqtt.broker}:{config.mqtt.port} (topic: {config.mqtt.topic_prefix}/#)"
    )
    logger.info("Storage Directories:")
    logger.info(f"  Media         : {config.storage.media_dir}")
    logger.info(f"  Telemetry Logs: {config.storage.sensor_logs_dir}")
    logger.info(f"  Compliance    : {config.storage.compliance_dir}")
    logger.info(
        f"Actuations      : {'ENABLED (Production)' if config.hardware.enable_hardware_control else 'DISABLED (Simulated)'}"
    )
    logger.info(f"  Aerator Pin   : {config.hardware.aerator_gpio_pin}")
    logger.info(f"  Pump Pin      : {config.hardware.pump_gpio_pin}")
    logger.info(f"  Valve Pin     : {config.hardware.valve_gpio_pin}")
    logger.info(f"  Alert Pin     : {config.hardware.alert_gpio_pin}")
    logger.info(
        f"Consent Rules   : {config.consent.regional_council} (ID: {config.consent.consent_id})"
    )
    logger.info("Thresholds:")
    logger.info(
        f"  pH            : {config.thresholds.ph_min} - {config.thresholds.ph_max}"
    )
    logger.info(f"  DO (min mg/L) : {config.thresholds.do_min}")
    logger.info(f"  Temp (max C)  : {config.thresholds.temp_max}")
    logger.info(f"  Turbidity NTU : {config.thresholds.turbidity_max}")
    logger.info(f"  Nitrate mg/L  : {config.thresholds.nitrate_max}")
    logger.info("=" * 60)
