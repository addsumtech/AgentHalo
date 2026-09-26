# AgentHalo 1.0.5

减少桌宠在任务状态更新时的阻塞和空闲时的后台查询，改进升级安装，并加强本地接口与浏览器桥接的输入检查。

## 修复与改进

- Codex 进程查询改为异步执行并复用缓存，避免查询阻塞桌宠主界面。
- WorkBuddy 没有活跃任务时停止轮询，兼容新版数据目录，并允许恢复的归档任务重新接收状态更新。
- 缓存 macOS 静音状态和 Node 路径检测结果，减少重复启动系统进程。
- VS Code／Cursor 终端定位扩展改为“设置 → 通用”中的可选开关；已有安装保留启用状态，升级时替换旧扩展副本。
- 首次迁移 Clawd on Desk 配置时改为复制，保留旧应用的设置和主题。
- npm 安装器增加下载停滞超时、失败与中断清理；确认新版复制完整且旧应用退出后再替换，替换失败时恢复旧版。
- 本地接口拒绝不受信任的网页请求；浏览器桥接校验消息来源和字段，应用窗口限制外部导航，“打开文件夹”拒绝可执行应用包。
- 启用 Electron 安全开关，移除安装包内已停用功能的代码与无用依赖，并补齐主题处理依赖。
- 补回 macOS 签名辅助脚本，修复依赖下载地址与测试兼容性，补充仓库自动检查。

## 安装或升级

```bash
npx agenthalo@latest
```

需要 macOS 和 Node.js 18 或更新版本。已有用户无需先卸载；安装器替换应用并保留用户设置和导入角色。

如果终端仍提示旧版本，可刷新官方源后安装：

```bash
npx --prefer-online --registry=https://registry.npmjs.org agenthalo@latest
```

手动下载：[Apple Silicon](https://github.com/addsumtech/AgentHalo/releases/download/v1.0.5/AgentHalo-1.0.5-arm64.dmg) · [Intel](https://github.com/addsumtech/AgentHalo/releases/download/v1.0.5/AgentHalo-1.0.5-x64.dmg)。同名 ZIP 包提供相同应用，校验和见附件 `SHA256SUMS.txt`。

使用浏览器桥接的用户，请在应用的“设置 → 连接应用”中更新扩展文件，再到浏览器扩展管理页重新加载扩展，并刷新聊天页面。已启用终端定位扩展的用户，重启 VS Code／Cursor 后加载新版扩展。

应用采用 ad-hoc 签名，尚未做 Apple 公证；手动下载后如被 macOS 阻止，请在“系统设置 → 隐私与安全性”选择“仍要打开”。

## 许可证

AGPL-3.0-only。基于 [Clawd on Desk](https://github.com/rullerzhou-afk/clawd-on-desk) 开发，保留上游版权和许可证。
