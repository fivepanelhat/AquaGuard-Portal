// AquaGuard-Portal/src/database/kv_store.js
// Local Key-Value store stub to mock session attestation database Lookups

const db = {
    nonces: {},
    keys: {}
};

module.exports = {
    getActiveNonce: async (deviceId) => {
        return db.nonces[deviceId] || null;
    },
    setActiveNonce: async (deviceId, nonce) => {
        db.nonces[deviceId] = nonce;
    },
    purgeNonce: async (deviceId) => {
        delete db.nonces[deviceId];
    },
    getDevicePublicKey: async (deviceId) => {
        return db.keys[deviceId] || null;
    },
    registerDeviceKey: async (deviceId, publicKeyPem) => {
        db.keys[deviceId] = publicKeyPem;
    }
};
