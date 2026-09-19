# AgentHalo 1.0.3

修复 Codex 后台记忆维护任务以 `memories` 出现在任务列表的问题。

## 修复内容

- 从第一条活动通知开始过滤已确认的后台记忆任务，不再等任务结束后才隐藏。
- 已出现的后台任务在后续活动到达时清理，不触发完成提醒。
- 结合 Codex 会话记录和实际记忆目录识别，保留用户创建的正常会话及同名项目。
- 会话数据库不可读取时保留原有显示行为，远程会话不使用本机目录判定。

## 安装或升级

```bash
npx agenthalo@latest
```

需要 macOS 和 Node.js 18 或更新版本。已有用户无需先卸载；安装器替换应用并保留用户设置和导入角色。

如果终端仍提示旧版本，可刷新官方源后安装：

```bash
npx --prefer-online --registry=https://registry.npmjs.org agenthalo@latest
```

手动下载：[Apple Silicon](https://github.com/addsumtech/AgentHalo/releases/download/v1.0.3/AgentHalo-1.0.3-arm64.dmg) · [Intel](https://github.com/addsumtech/AgentHalo/releases/download/v1.0.3/AgentHalo-1.0.3-x64.dmg)。同名 ZIP 包提供相同应用，校验和见附件 `SHA256SUMS.txt`。

浏览器扩展仍为 v0.3.3，无需重新安装。应用目前采用 ad-hoc 签名，尚未做 Apple 公证；手动下载后如被 macOS 阻止，请在“系统设置 → 隐私与安全性”选择“仍要打开”。

## 许可证

AGPL-3.0-only。基于 [Clawd on Desk](https://github.com/rullerzhou-afk/clawd-on-desk) 开发，保留上游版权和许可证。
