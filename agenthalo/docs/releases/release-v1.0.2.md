# AgentHalo 1.0.2

修复 Codex 任务列表中多出一个以工作文件夹命名的重复任务。

## 修复内容

- Codex 生成带分段后缀的新日志文件时，继续识别为原来的会话。
- 优先读取日志元数据中的真实会话编号，避免丢失任务标题、误显示工作文件夹名。
- 同步修正重启恢复和归档时的会话编号识别。
- 补齐仓库缺失的开发检查脚本，修复全量测试的两个启动失败。

## 安装或升级

```bash
npx agenthalo@latest
```

需要 macOS 和 Node.js 18 或更新版本。已有用户无需先卸载；安装器替换应用并保留用户设置和导入角色。

如果终端仍提示旧版本，可刷新官方源后安装：

```bash
npx --prefer-online --registry=https://registry.npmjs.org agenthalo@latest
```

手动下载：[Apple Silicon](https://github.com/addsumtech/AgentHalo/releases/download/v1.0.2/AgentHalo-1.0.2-arm64.dmg) · [Intel](https://github.com/addsumtech/AgentHalo/releases/download/v1.0.2/AgentHalo-1.0.2-x64.dmg)。同名 ZIP 包提供相同应用，校验和见附件 `SHA256SUMS.txt`。

浏览器扩展仍为 v0.3.3，无需重新安装。应用目前采用 ad-hoc 签名，尚未做 Apple 公证；手动下载后如被 macOS 阻止，请在“系统设置 → 隐私与安全性”选择“仍要打开”。

## 许可证

AGPL-3.0-only。基于 [Clawd on Desk](https://github.com/rullerzhou-afk/clawd-on-desk) 开发，保留上游版权和许可证。
