// AquaGuard-Portal/src/routes/actuators.js
const express = require('express');
const router = express.Router();
const { verifyNodeAttestation } = require('@fivepanelhat/coastal-alpine-core');
const { getDevicePublicKey, getActiveNonce, purgeNonce } = require('../database/kv_store');

// Mock command execution functions to allow validation out-of-the-box
function executeMqttCommand(deviceId, command) {
    console.log(`[MQTT ACTUATION] Dispatching command [${command}] to verified node [${deviceId}].`);
}

function triggerSecurityIsolationAlert(deviceId) {
    console.error(`[SECOPS LOCKDOWN] ALERT: Hardware verification failed for node [${deviceId}]! Triggering site isolation alarms.`);
}

router.post('/actuate/valve', async (req, res) => {
    const { deviceId, attestationPayload, command } = req.body;
    
    // 1. Retrieve the single-use challenge nonce issued to this device during its check-in
    const activeNonce = await getActiveNonce(deviceId);
    if (!activeNonce) {
        return res.status(401).json({ error: "Missing active attestation session context." });
    }
    
    // Consume the nonce instantly so it can never be processed again
    await purgeNonce(deviceId);

    // 2. Fetch the device's unique physical public key stored during staging
    const devicePublicKey = await getDevicePublicKey(deviceId);

    // 3. Pass values to the Core Validator Layer
    const isNodePristine = verifyNodeAttestation(activeNonce, attestationPayload, devicePublicKey);

    if (isNodePristine) {
        // Safe to execute physical actuation logic
        executeMqttCommand(deviceId, command);
        return res.json({ status: "Command routed to verified pristine node." });
    } else {
        // Trigger site isolation lockdown alarms
        triggerSecurityIsolationAlert(deviceId);
        return res.status(403).json({ error: "Hardware verification failed. Command dropped." });
    }
});

module.exports = router;
