"""
portal_core/mqtt_client.py - MQTT Client Module for AquaGuard Portal.

Manages connection to Mosquitto broker and registers subscriptions for water sensors.
"""

import asyncio
import json
import logging
from typing import Optional
from datetime import datetime
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MQTTClient:
    """
    Subscribes to water sensor telemetry topics (e.g. pH, DO, temperature, turbidity, nitrate).
    Runs as an async wrapper around standard Paho MQTT.
    """

    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        client_id: str = "aquaguard-portal",
        topic_prefix: str = "aquaguard/sensors",
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id
        self.topic_prefix = topic_prefix.rstrip('/')
        self.username = username
        self.password = password
        self.client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
        self.connected = False
        self.message_queue: asyncio.Queue = asyncio.Queue()

        if username and password:
            self.client.username_pw_set(username, password)

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        logger.info(
            f"MQTT Client configured: {broker_host}:{broker_port} "
            f"(id={client_id}, auth={'enabled' if username else 'disabled'}, topic_prefix={self.topic_prefix})"
        )

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            logger.info("✓ Connected to MQTT Broker successfully.")
            # Subscribe to all telemetry sensors matching the prefix
            topic = f"{self.topic_prefix}/#"
            self.client.subscribe(topic)
            logger.info(f"Subscribed to topic: {topic}")
        else:
            logger.error(f"✗ MQTT connection failed with result code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected MQTT broker disconnection: {rc}")

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            logger.debug(f"MQTT message received on topic '{msg.topic}': {payload}")
            
            # Enqueue the parsed telemetry frame
            asyncio.run_coroutine_threadsafe(
                self.message_queue.put({
                    "topic": msg.topic,
                    "payload": payload,
                    "timestamp": datetime.now().isoformat()
                }),
                asyncio.get_event_loop()
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed decoding JSON payload on topic '{msg.topic}': {e}")
        except Exception as e:
            logger.error(f"Error handling message on topic '{msg.topic}': {e}")

    async def connect(self) -> bool:
        """
        Attempts connection to the broker with exponential retries.
        """
        max_retries = 3
        delay = 2

        for attempt in range(max_retries):
            try:
                self.client.connect(self.broker_host, self.broker_port, keepalive=60)
                self.client.loop_start()
                logger.info("MQTT connection loop initiated.")
                return True
            except Exception as e:
                logger.error(f"MQTT connection attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)
                    delay *= 2

        logger.error("Failed to connect to MQTT broker; check configuration.")
        return False

    async def disconnect(self):
        """Clean shutdown of client loops."""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT client disconnected successfully.")
        except Exception as e:
            logger.error(f"Error disconnecting MQTT client: {e}")

    async def read_message(self) -> dict:
        """Retrieve the next queued telemetry reading."""
        return await self.message_queue.get()

    async def health_check(self) -> bool:
        """Check active broker connection state."""
        return self.connected
