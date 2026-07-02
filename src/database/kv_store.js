// AquaGuard-Portal/src/database/kv_store.js
// Durable attestation state store (SQLite). Replaces the in-memory mock.
// API-compatible with the original stub: all methods async, same names.
// Offline-first: single local file, WAL mode, zero network dependencies.
"use strict";

const path = require("path");
const fs = require("fs");
const crypto = require("crypto");
const Database = require("better-sqlite3");

const DB_PATH = process.env.AQUAGUARD_DB_PATH
    || path.join(__dirname, "..", "..", "data", "aquaguard_attestation.db");
const NONCE_TTL_MS = parseInt(process.env.AQUAGUARD_NONCE_TTL_MS || "120000", 10);

fs.mkdirSync(path.dirname(DB_PATH), { recursive: true });

const db = new Database(DB_PATH);
db.pragma("journal_mode = WAL");
db.pragma("synchronous = NORMAL");

db.exec(`
CREATE TABLE IF NOT EXISTS attestation_nonces (
    device_id  TEXT PRIMARY KEY,
    nonce      TEXT NOT NULL,
    issued_at  INTEGER NOT NULL,
    expires_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS device_keys (
    device_id    TEXT PRIMARY KEY,
    public_key_pem TEXT NOT NULL,
    registered_at  INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_nonces_expiry ON attestation_nonces(expires_at);
`);

// Auto-cleanup: purge expired nonces on startup and every 60s
function cleanupExpiredNonces() {
    const now = Date.now();
    db.prepare("DELETE FROM attestation_nonces WHERE expires_at < ?").run(now);
}

cleanupExpiredNonces();
setInterval(cleanupExpiredNonces, 60000);

module.exports = {
    getActiveNonce: async (deviceId) => {
        const now = Date.now();
        const row = db.prepare(
            "SELECT nonce FROM attestation_nonces WHERE device_id = ? AND expires_at > ?"
        ).get(deviceId, now);
        return row ? row.nonce : null;
    },

    setActiveNonce: async (deviceId, nonce) => {
        const now = Date.now();
        const expiresAt = now + NONCE_TTL_MS;
        db.prepare(
            "INSERT OR REPLACE INTO attestation_nonces (device_id, nonce, issued_at, expires_at) VALUES (?, ?, ?, ?)"
        ).run(deviceId, nonce, now, expiresAt);
    },

    purgeNonce: async (deviceId) => {
        db.prepare("DELETE FROM attestation_nonces WHERE device_id = ?").run(deviceId);
    },

    getDevicePublicKey: async (deviceId) => {
        const row = db.prepare("SELECT public_key_pem FROM device_keys WHERE device_id = ?").get(deviceId);
        return row ? row.public_key_pem : null;
    },

    registerDeviceKey: async (deviceId, publicKeyPem) => {
        const now = Date.now();
        db.prepare(
            "INSERT OR REPLACE INTO device_keys (device_id, public_key_pem, registered_at) VALUES (?, ?, ?)"
        ).run(deviceId, publicKeyPem, now);
    }
};
