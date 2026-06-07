# AquaGuard Portal: Development Guide

## Local Development Setup

```bash
git clone https://github.com/fivepanelhat/AquaGuard-Portal.git
cd AquaGuard-Portal
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
```

## Running Tests

```bash
pytest tests/ -v
```

## Mocking MQTT in Development

Set `MQTT_MOCK=true` in `.env` to run the portal without a live broker.
The mock publisher in `tests/mock_mqtt.py` simulates ESP32 sensor payloads.

## Linting and Formatting

```bash
black .
flake8 .
mypy .
```
