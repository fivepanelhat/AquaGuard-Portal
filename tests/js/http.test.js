// AquaGuard-Portal/tests/js/http.test.js
// Basic smoke tests for Express server endpoints
"use strict";

const test = require("node:test");
const assert = require("node:assert");
const http = require("http");

const PORT = process.env.PORT || 3000;
const BASE_URL = `http://localhost:${PORT}`;

// Helper: make HTTP request
function makeRequest(method, path, body = null) {
 return new Promise((resolve, reject) => {
 const url = new URL(path, BASE_URL);
 const options = {
 hostname: url.hostname,
 port: url.port,
 path: url.pathname + url.search,
 method,
 headers: {
 "Content-Type": "application/json"
 }
 };

 const req = http.request(options, (res) => {
 let data = "";
 res.on("data", (chunk) => data += chunk);
 res.on("end", () => {
 try {
 resolve({
 status: res.statusCode,
 headers: res.headers,
 body: data ? JSON.parse(data) : null
 });
 } catch (e) {
 resolve({
 status: res.statusCode,
 headers: res.headers,
 body: data
 });
 }
 });
 });

 req.on("error", reject);
 if (body) req.write(JSON.stringify(body));
 req.end();
 });
}

test("Health check endpoint", async () => {
 const res = await makeRequest("GET", "/health");
 assert.strictEqual(res.status, 200);
 assert.ok(res.body.status);
 assert.ok(res.body.timestamp);
});

test("POST /api/nonce-challenge with valid deviceId", async () => {
 const res = await makeRequest("POST", "/api/nonce-challenge", {
 deviceId: "test-device-001"
 });
 assert.strictEqual(res.status, 200);
 assert.ok(res.body.nonce);
 assert.strictEqual(res.body.nonce.length, 64); // 32 bytes hex = 64 chars
});

test("POST /api/nonce-challenge without deviceId", async () => {
 const res = await makeRequest("POST", "/api/nonce-challenge", {});
 assert.strictEqual(res.status, 400);
 assert.ok(res.body.error);
});

test("POST /api/telemetry with valid payload", async () => {
 const res = await makeRequest("POST", "/api/telemetry", {
 deviceId: "test-device-001",
 readings: [
 { ph: 7.2, do: 8.5, temperature: 22.1 }
 ]
 });
 assert.strictEqual(res.status, 200);
 assert.ok(res.body.status);
});

test("POST /api/actuate/valve without nonce", async () => {
 const res = await makeRequest("POST", "/api/actuate/valve", {
 deviceId: "test-device-001",
 attestationPayload: {},
 command: "OPEN"
 });
 assert.strictEqual(res.status, 401);
 assert.ok(res.body.error);
});

test("404 for unknown route", async () => {
 const res = await makeRequest("GET", "/api/nonexistent");
 assert.strictEqual(res.status, 404);
 assert.ok(res.body.error);
});

console.log("All tests passed!");
