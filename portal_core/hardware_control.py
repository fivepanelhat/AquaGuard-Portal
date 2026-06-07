"""
portal_core/hardware_control.py - Hardware Control Module for AquaGuard Portal.

Manages GPIO/PWM controllers for aerators, water circulation pumps, valves, and alarms.
Includes full software simulation fallbacks for development/test loops.
"""

import asyncio
import logging
from typing import Optional, List, Dict
from datetime import datetime
from portal_schemas.compliance import AerationAction, PumpAction, ValveAction

logger = logging.getLogger(__name__)

# Attempt importing physical GPIO module
try:
    import RPi.GPIO as GPIO  # type: ignore
    ENABLE_GPIO = True
except ImportError:
    ENABLE_GPIO = False
    logger.warning("RPi.GPIO is unavailable; hardware control will operate in simulation mode.")


class HardwareControl:
    """
    Manages GPIO states for:
    - Aerator (PWM duty cycles)
    - Water Pump (PWM duty cycles)
    - Effluent Valve (digital open/closed)
    - Alert Buzzer / Relay (digital high/low)
    """

    def __init__(
        self,
        aerator_gpio_pin: Optional[int] = None,
        pump_gpio_pin: Optional[int] = None,
        valve_gpio_pin: Optional[int] = None,
        alert_gpio_pin: Optional[int] = None,
        enable_hardware_control: bool = False,
    ):
        self.aerator_gpio_pin = aerator_gpio_pin
        self.pump_gpio_pin = pump_gpio_pin
        self.valve_gpio_pin = valve_gpio_pin
        self.alert_gpio_pin = alert_gpio_pin

        # Enforce simulation mode if GPIO libraries are missing
        self.simulation_mode = not enable_hardware_control or not ENABLE_GPIO

        # Active state registers
        self.aerator_state = AerationAction.OFF
        self.aerator_duty_cycle = 0
        self.pump_state = PumpAction.OFF
        self.pump_duty_cycle = 0
        self.valve_state = ValveAction.CLOSED

        # PWM references
        self.aerator_pwm = None
        self.pump_pwm = None

        # Auditing log trail
        self.action_history: List[Dict] = []

        logger.info(
            f"Hardware Control configured: aerator_pin={aerator_gpio_pin}, pump_pin={pump_gpio_pin}, "
            f"valve_pin={valve_gpio_pin}, alert_pin={alert_gpio_pin}, simulation={self.simulation_mode}"
        )

    async def setup(self):
        """Initialise hardware pins and default low signals."""
        if self.simulation_mode:
            logger.info("Hardware Control setup finished in simulation mode.")
            return

        try:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)

            if self.aerator_gpio_pin:
                GPIO.setup(self.aerator_gpio_pin, GPIO.OUT)
                self.aerator_pwm = GPIO.PWM(self.aerator_gpio_pin, 1000)
                self.aerator_pwm.start(0)
                logger.info(f"Aerator GPIO pin {self.aerator_gpio_pin} setup with PWM.")

            if self.pump_gpio_pin:
                GPIO.setup(self.pump_gpio_pin, GPIO.OUT)
                self.pump_pwm = GPIO.PWM(self.pump_gpio_pin, 1000)
                self.pump_pwm.start(0)
                logger.info(f"Pump GPIO pin {self.pump_gpio_pin} setup with PWM.")

            if self.valve_gpio_pin:
                GPIO.setup(self.valve_gpio_pin, GPIO.OUT)
                GPIO.output(self.valve_gpio_pin, GPIO.LOW)
                logger.info(f"Valve GPIO pin {self.valve_gpio_pin} setup.")

            if self.alert_gpio_pin:
                GPIO.setup(self.alert_gpio_pin, GPIO.OUT)
                GPIO.output(self.alert_gpio_pin, GPIO.LOW)
                logger.info(f"Alert GPIO pin {self.alert_gpio_pin} setup.")

            logger.info("✓ Hardware Control Setup successfully.")
        except Exception as e:
            logger.error(f"✗ Failed setting up GPIO pins: {e}. Enabling simulation fallback.")
            self.simulation_mode = True

    async def cleanup(self):
        """Reset pin outputs and shutdown PWM clocks."""
        if self.simulation_mode or not ENABLE_GPIO:
            return

        try:
            if self.aerator_pwm:
                self.aerator_pwm.stop()
            if self.pump_pwm:
                self.pump_pwm.stop()
            GPIO.cleanup()
            logger.info("GPIO cleanup finished successfully.")
        except Exception as e:
            logger.error(f"Error executing GPIO cleanup: {e}")

    async def set_aerator(self, state: AerationAction) -> bool:
        try:
            duty_map = {
                AerationAction.OFF: 0,
                AerationAction.LOW: 30,
                AerationAction.MEDIUM: 60,
                AerationAction.HIGH: 100
            }
            dc = duty_map.get(state, 0)
            self.aerator_state = state
            self.aerator_duty_cycle = dc

            if self.simulation_mode:
                logger.info(f"[SIM] Aerator state -> {state.value} (PWM {dc}%)")
            else:
                if self.aerator_pwm:
                    self.aerator_pwm.ChangeDutyCycle(dc)
                    logger.info(f"Aerator state -> {state.value} (PWM {dc}%)")

            self._record_action("aerator", state.value, dc)
            return True
        except Exception as e:
            logger.error(f"Error setting aerator output: {e}")
            return False

    async def set_pump(self, state: PumpAction) -> bool:
        try:
            duty_map = {
                PumpAction.OFF: 0,
                PumpAction.LOW: 33,
                PumpAction.MEDIUM: 66,
                PumpAction.HIGH: 100
            }
            dc = duty_map.get(state, 0)
            self.pump_state = state
            self.pump_duty_cycle = dc

            if self.simulation_mode:
                logger.info(f"[SIM] Water Pump state -> {state.value} (PWM {dc}%)")
            else:
                if self.pump_pwm:
                    self.pump_pwm.ChangeDutyCycle(dc)
                    logger.info(f"Water Pump state -> {state.value} (PWM {dc}%)")

            self._record_action("pump", state.value, dc)
            return True
        except Exception as e:
            logger.error(f"Error setting water pump output: {e}")
            return False

    async def set_valve(self, state: ValveAction) -> bool:
        try:
            self.valve_state = state
            val = 1 if state == ValveAction.OPEN else 0

            if self.simulation_mode:
                logger.info(f"[SIM] Valve state -> {state.value} (pin value {val})")
            else:
                if self.valve_gpio_pin:
                    GPIO.output(self.valve_gpio_pin, GPIO.HIGH if val == 1 else GPIO.LOW)
                    logger.info(f"Valve state -> {state.value} (pin value {val})")

            self._record_action("valve", state.value, val)
            return True
        except Exception as e:
            logger.error(f"Error setting valve output: {e}")
            return False

    async def trigger_alert(self, duration_ms: int = 500):
        try:
            if self.simulation_mode:
                logger.warning(f"[SIM] Alert relay triggered for {duration_ms}ms.")
            else:
                if self.alert_gpio_pin:
                    GPIO.output(self.alert_gpio_pin, GPIO.HIGH)
                    await asyncio.sleep(duration_ms / 1000.0)
                    GPIO.output(self.alert_gpio_pin, GPIO.LOW)
                    logger.warning(f"Alert relay triggered for {duration_ms}ms.")

            self._record_action("alert", "triggered", duration_ms)
        except Exception as e:
            logger.error(f"Error triggering alert pin: {e}")

    async def enforce_plan(self, plan: dict) -> bool:
        """
        Translates a Pydantic-validated WaterOptimizationPlan dict into pin signals.
        """
        try:
            logger.info(f"Enforcing action plan: {plan.get('plan_id', 'unknown')}")
            
            aeration_action = plan.get("aeration_action")
            pump_action = plan.get("pump_action")
            valve_action = plan.get("valve_action")

            success = True

            if aeration_action:
                state = AerationAction(aeration_action.lower() if isinstance(aeration_action, str) else aeration_action)
                ok = await self.set_aerator(state)
                success = success and ok

            if pump_action:
                state = PumpAction(pump_action.lower() if isinstance(pump_action, str) else pump_action)
                ok = await self.set_pump(state)
                success = success and ok

            if valve_action:
                state = ValveAction(valve_action.lower() if isinstance(valve_action, str) else valve_action)
                ok = await self.set_valve(state)
                success = success and ok

            if plan.get("requires_human_review"):
                await self.trigger_alert(1000)

            logger.info(f"Plan enforcement concluded with status: {success}")
            return success
        except Exception as e:
            logger.error(f"Error executing plan enforcement: {e}")
            return False

    def _record_action(self, device: str, action: str, value: int):
        self.action_history.append({
            "timestamp": datetime.now().isoformat(),
            "device": device,
            "action": action,
            "value": value
        })
        if len(self.action_history) > 1000:
            self.action_history.pop(0)

    def get_status(self) -> dict:
        return {
            "aerator": {
                "state": self.aerator_state.value,
                "duty_cycle_pct": self.aerator_duty_cycle
            },
            "pump": {
                "state": self.pump_state.value,
                "duty_cycle_pct": self.pump_duty_cycle
            },
            "valve": {
                "state": self.valve_state.value
            },
            "simulation_mode": self.simulation_mode,
            "timestamp": datetime.now().isoformat()
        }

    async def health_check(self) -> bool:
        if not self.simulation_mode:
            return bool(self.aerator_gpio_pin or self.pump_gpio_pin or self.valve_gpio_pin)
        return True
