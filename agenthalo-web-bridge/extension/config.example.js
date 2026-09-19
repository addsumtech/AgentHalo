// AgentHalo custom agent IDs. Chrome Web Store and packaged copies leave these
// blank — the extension asks the running desktop app on GET /web-bridge.
const CLAWD_WEB_BRIDGE_CONFIG = {
  agents: {
    "claude-web": "",
    "chatgpt-web": "",
    "gemini-web": ""
  },
  // AgentHalo binds 127.0.0.1 and picks the first free port in this range.
  ports: [23333, 23334, 23335, 23336, 23337],
  workingAfterMs: 2500,
  heartbeatMs: 45000,
  pollMs: 500
};
if (typeof globalThis !== "undefined") globalThis.CLAWD_WEB_BRIDGE_CONFIG = CLAWD_WEB_BRIDGE_CONFIG;
