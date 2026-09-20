# AgentHalo 1.0.4

修复 Cursor 空会话以项目文件夹名出现在任务列表、一直显示“等待中”的问题。

## 修复内容

- 仅创建或打开 Cursor 会话时，不再创建任务条目；收到实际提问、思考或工具活动后才显示。
- 保留空会话的来源识别，避免稍后的正常活动被误判为其他任务的子 agent。
- 延迟到达的会话开始通知不再把正在执行的任务重置为等待。
- 保留现有 Cursor 子 agent 过滤，其他应用的会话显示规则不变。

## 安装或升级

```bash
npx agenthalo@latest
```

需要 macOS 和 Node.js 18 或更新版本。已有用户无需先卸载；安装器替换应用并保留用户设置和导入角色。

如果终端仍提示旧版本，可刷新官方源后安装：

```bash
npx --prefer-online --registry=https://registry.npmjs.org agenthalo@latest
```

手动下载：[Apple Silicon](https://github.com/addsumtech/AgentHalo/releases/download/v1.0.4/AgentHalo-1.0.4-arm64.dmg) · [Intel](https://github.com/addsumtech/AgentHalo/releases/download/v1.0.4/AgentHalo-1.0.4-x64.dmg)。同名 ZIP 包提供相同应用，校验和见附件 `SHA256SUMS.txt`。

浏览器扩展仍为 v0.3.3，无需重新安装。应用目前采用 ad-hoc 签名，尚未做 Apple 公证；手动下载后如被 macOS 阻止，请在“系统设置 → 隐私与安全性”选择“仍要打开”。

## 许可证

AGPL-3.0-only。基于 [Clawd on Desk](https://github.com/rullerzhou-afk/clawd-on-desk) 开发，保留上游版权和许可证。
