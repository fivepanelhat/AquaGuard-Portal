# AquaGuard Portal: Getting Started

This guide extends the Quick Start in README.md with additional configuration detail.

---

## 1. Environment Configuration

Copy `.env.example` to `.env` and configure:

---

## 2. Consent Threshold Configuration

Edit the threshold block in `.env` to match your specific resource consent conditions:

Consult your regional council consent document for the correct values for your site.

---

## 3. Running as a Systemd Service

```bash
sudo cp aquaguard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable aquaguard
sudo systemctl start aquaguard
sudo systemctl status aquaguard
```

---

## 4. Checking Compliance Exports

Compliance records are written to `telemetry_data/compliance_exports/` as timestamped JSON and CSV files.
Review these before council inspections or Farm Plan audits.
