// AquaGuard-Portal/server.js
// Express HTTP server for attested device actuation + telemetry ingestion.
// Integrates coastal-alpine-core TPM 2.0 attestation validator with offline-first SQLite nonce store.
"use strict";

const express = require("express");
const path = require("path");
const crypto = require("crypto");
const rateLimit = require("express-rate-limit");
const { verifyNodeAttestation } = require("@fivepanelhat/coastal-alpine-core");
const kvStore = require("./src/database/kv_store");

const app = express();
const PORT = parseInt(process.env.PORT || "3000", 10);
const RATE_WINDOW_MS = parseInt(process.env.RATE_LIMIT_WINDOW_MS || "900000", 10);
const RATE_MAX_REQUESTS = parseInt(process.env.RATE_LIMIT_MAX_REQUESTS || "50", 10);

// Middleware
app.use(express.json({ limit: "10kb" }));

// Rate limiting: 50 requests per 15 minutes per IP
const rateLimiter = rateLimit({
 windowMs: RATE_WINDOW_MS,
 max: RATE_MAX_REQUESTS,
 standardHeaders: true,
 legacyHeaders: false,
 message: "Too many requests, please try again later.",
 store: new rateLimit.MemoryStore()
});

app.use("/api/", rateLimiter);

// Health check
app.get("/health", (req, res) => {
 res.json({ status: "ok", timestamp: new Date().toISOString() });
});

// POST /api/actuate/valve
// Expects: { deviceId, attestationPayload, command }
// Returns: { status: "..." } or error 403
app.post("/api/actuate/valve", async (req, res) => {
 try {
 const { deviceId, attestationPayload, command } = req.body;

 if (!deviceId || !attestationPayload || !command) {
 return res.status(400).json({ error: "Missing required fields: deviceId, attestationPayload, command" });
 }

 // 1. Retrieve single-use nonce
 const activeNonce = await kvStore.getActiveNonce(deviceId);
 if (!activeNonce) {
 return res.status(401).json({ error: "Missing active attestation session context." });
 }

 // 2. Consume nonce immediately (single-use guarantee)
 await kvStore.purgeNonce(deviceId);

 // 3. Fetch device's public key
 const devicePublicKey = await kvStore.getDevicePublicKey(deviceId);
 if (!devicePublicKey) {
 return res.status(401).json({ error: "Device not registered." });
 }

 // 4. Verify TPM 2.0 attestation via coastal-alpine-core
 const isNodePristine = verifyNodeAttestation(activeNonce, attestationPayload, devicePublicKey);

 if (!isNodePristine) {
 console.error(`[SECOPS] Hardware verification FAILED for device [${deviceId}]. Triggering isolation.`);
 return res.status(403).json({ error: "Hardware verification failed. Command dropped." });
 }

 // 5. Route command via MQTT (stub for now)
 console.log(`[ACTUATION OK] Device [${deviceId}] verified pristine. Dispatching command: ${command}`);
 executeMqttCommand(deviceId, command);

 res.json({ status: "Command routed to verified pristine node." });
 } catch (error) {
 console.error(`[HTTP ERROR] /api/actuate/valve: ${error.message}`);
 res.status(500).json({ error: "Internal server error." });
 }
});

// POST /api/telemetry
// Accepts sensor readings from verified nodes (rate-limited)
app.post("/api/telemetry", async (req, res) => {
 try {
 const { deviceId, readings } = req.body;
 if (!deviceId || !readings) {
 return res.status(400).json({ error: "Missing deviceId or readings." });
 }

 console.log(`[TELEMETRY] Ingested ${readings.length} readings from device [${deviceId}].`);
 // In production: persist to time-series database
 res.json({ status: "Telemetry ingested." });
 } catch (error) {
 console.error(`[HTTP ERROR] /api/telemetry: ${error.message}`);
 res.status(500).json({ error: "Internal server error." });
 }
});

// POST /api/nonce-challenge
// Issues a single-use nonce for device attestation handshake
app.post("/api/nonce-challenge", async (req, res) => {
 try {
 const { deviceId } = req.body;
 if (!deviceId) {
 return res.status(400).json({ error: "Missing deviceId." });
 }

 const nonce = crypto.randomBytes(32).toString("hex");
 await kvStore.setActiveNonce(deviceId, nonce);

 console.log(`[NONCE] Issued challenge for device [${deviceId}].`);
 res.json({ nonce });
 } catch (error) {
 console.error(`[HTTP ERROR] /api/nonce-challenge: ${error.message}`);
 res.status(500).json({ error: "Internal server error." });
 }
});

// 404 handler
app.use((req, res) => {
 res.status(404).json({ error: "Not found." });
});

// Mock MQTT dispatch (replace with real MQTT client in production)
function executeMqttCommand(deviceId, command) {
 console.log(`[MQTT STUB] Would dispatch to ${deviceId}: ${command}`);
 // In production: connect to MQTT broker and publish to device topic
}

// Startup
app.listen(PORT, () => {
 console.log(`[STARTUP] AquaGuard HTTP server listening on port ${PORT}`);
 console.log(`[CONFIG] Rate limit: ${RATE_MAX_REQUESTS} requests per ${RATE_WINDOW_MS}ms`);
 console.log(`[CONFIG] Attestation nonce TTL: ${process.env.AQUAGUARD_NONCE_TTL_MS || "120000"}ms`);
});

module.exports = app;
