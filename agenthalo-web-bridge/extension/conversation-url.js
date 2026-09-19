// Shared by the service worker and content script. Temporary chats have no
// route ID, so their mode parameter is part of the conversation identity.
function clawdConversationUrl(value) {
  try {
    const url = new URL(value);
    const key = url.hostname === "claude.ai" ? "incognito"
      : /^(chatgpt\.com|chat\.openai\.com)$/.test(url.hostname) ? "temporary-chat" : null;
    const mode = key && url.searchParams.has(key)
      ? `?${key}=${encodeURIComponent(url.searchParams.get(key))}` : "";
    return url.origin + url.pathname + mode;
  } catch { return null; }
}
globalThis.clawdConversationUrl = clawdConversationUrl;
