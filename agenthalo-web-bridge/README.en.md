# AgentHalo Web Bridge

English · [简体中文](README.md)

Show generation activity from Claude, ChatGPT, and Gemini web conversations in your AgentHalo desktop companion.

[Download extension v0.3.3](https://github.com/addsumtech/AgentHalo/releases/download/web-bridge-v0.3.3/AgentHalo-Web-Bridge.zip)

## Install on macOS

Requires AgentHalo, Node.js 22 or later, and Chrome or Edge.

1. Download `AgentHalo-Web-Bridge.zip` and extract it to any temporary folder. The setup script copies the extension into a stable application data directory.
2. Launch AgentHalo at least once, then choose **Quit** from its menu.
3. Open Terminal in the extracted `AgentHalo-Web-Bridge` folder and run:

   ```sh
   node scripts/register.js
   ```

   This backs up AgentHalo preferences, registers the three web applications, creates a local configuration, and installs the extension into `~/Library/Application Support/AgentHalo/WebBridge/extension`. Existing enablement and notification preferences are preserved. If AgentHalo is running, the script stops and asks you to quit it.

4. Open AgentHalo again.
5. In Chrome, open `chrome://extensions`; in Edge, open `edge://extensions`. Enable **Developer mode**, click **Load unpacked**, and select `~/Library/Application Support/AgentHalo/WebBridge/extension`. In the folder picker, press `⌘⇧G`, paste this path, and press Return.
6. Refresh any open chat pages. Send a message, then open **Task list** from the companion menu to see its session.

The download is public. The package contains no local registration IDs, preferences, credentials, or runtime logs.

## Update

The current extension version is **0.3.3**. Quit AgentHalo and run `node scripts/register.js` from the new download. The script preserves the installed local configuration and updates the stable installation folder. Open AgentHalo, reload the extension in your browser, and refresh the chat pages. Run registration again on another computer or user account. If you move the installation folder, remove the old extension and load it again from the new location.

## Behavior and troubleshooting

- Generation starts in the thinking state and switches to working after 2.5 seconds. Completed replies enter waiting; closing a tab or switching conversations clears the old task card.
- Each tab has its own session. Duplicated tabs do not share sessions, and background service restarts preserve tab mappings.
- On macOS, clicking a task card first looks for the existing browser tab before opening a new one.
- The extension reports activity only and does not handle permission approvals. It reads the current conversation URL, title, and generation state.
- It detects AgentHalo on local ports 23333–23337. If connection fails, check that AgentHalo is running, then inspect the extension service worker log.
- Claude Code web mode and Codex cloud tasks are outside the extension's scope. Local Codex is connected by AgentHalo itself.
- Qianwen detection code is included, but the setup script does not register it and it has not been verified in the current release. Qwen Code and QwenWork use AgentHalo's native hooks.
- Website changes can affect detection. This release has automated state-machine and package checks; it does not claim a new live conversation test on all three sites.

## License

AGPL-3.0-only. See `LICENSE` and `NOTICE.md` in the download. The extension runtime source code is included in the package.
