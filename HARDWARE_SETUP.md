# AquaGuard Portal: Hardware Setup Guide

**Coastal Alpine Tech Limited** — New Plymouth, Taranaki

---

## Bill of Materials (NZ-available)

| Component | Spec | NZ Supplier |
|---|---|---|
| Raspberry Pi 5 | 16GB RAM | PB Tech, Kiwi Electronics |
| Raspberry Pi AI HAT+ | Hailo-10H NPU, 40 TOPS | PB Tech, Kiwi Electronics |
| Water quality sensor kit | pH, DO, temperature, turbidity | Atlas Scientific, DFRobot via AliExpress |
| ESP32 gateway | WiFi/MQTT | Jaycar, Kiwi Electronics |
| IP67/IP68 enclosure | Sensor housing | RS Components NZ |
| CSI camera module | Underwater housing | PB Tech |
| Hydrophone (optional) | Acoustic anomaly detection | Specialist supplier |

---

## Raspberry Pi AI HAT+ Installation

1. Power down the Pi 5 completely.
2. Attach the AI HAT+ to the M.2 HAT+ connector on the underside of the Pi 5 board.
3. Secure with the provided standoffs.
4. Install Hailo drivers:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install hailo-all -y
sudo reboot
```

5. Verify NPU detection:

```bash
hailortcli fw-control identify
```

Expected output: `Hailo-10H device detected`.

---

## Sensor Wiring (ESP32 → MQTT)

Connect sensors to ESP32 GPIO pins per your sensor datasheet.
Flash the ESP32 with the MQTT publisher firmware in `portal_core/esp32_firmware/`.
Configure `MQTT_BROKER_HOST` in `.env` to match your local Mosquitto broker IP.

---

## IP-Rating Guidance

All sensor assemblies deployed in or near water must be housed in **IP67-rated** enclosures minimum.
For submerged components, use **IP68-rated** enclosures.
Seal all cable entry points with marine-grade gland fittings.

---

## Sensor Calibration Schedule

| Sensor | Calibration Interval | Method |
|---|---|---|
| pH probe | 12 months | Two-point buffer calibration (pH 4.0 and 7.0) |
| DO probe | 3–6 months | Air-saturation and zero-oxygen calibration |
| Turbidity | 6 months | Formazin standard solutions |

*Always log calibration dates and readings in `telemetry_data/sensor_logs/calibration_log.json`.*
