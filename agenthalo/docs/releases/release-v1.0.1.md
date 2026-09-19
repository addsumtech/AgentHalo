# AgentHalo 1.0.1

这次更新让设置入口、角色导入和浏览器扩展安装更清楚。

## 更新内容

- 新安装默认显示 Dock 图标，点击即可打开设置主界面；已有用户的显示偏好保持不变。
- 桌面伙伴统一为“导入角色包”，自动识别 AgentHalo 和 Codex Pet 格式，入口移至角色列表下方。
- 简化设置页的边框、配色和按钮层级。
- “下载扩展包”改为醒目的主按钮，“安装指引”提供浏览器选择和分步说明。
- 未收到网页状态时显示“扩展已安装，请在 AI 网页中发起一次对话”；详情中的安装状态不再混用等待提示。
- 同步全部七种界面语言。

## 安装或更新

```bash
npx agenthalo@latest
```

需要 macOS 和 Node.js 18 或更新版本。安装器会识别芯片、校验下载文件，并替换已有应用；用户偏好和导入角色保留。

也可以手动下载：

| Mac 芯片 | 安装包 |
| --- | --- |
| Apple Silicon（M 系列） | [AgentHalo-1.0.1-arm64.dmg](https://github.com/addsumtech/AgentHalo/releases/download/v1.0.1/AgentHalo-1.0.1-arm64.dmg) |
| Intel | [AgentHalo-1.0.1-x64.dmg](https://github.com/addsumtech/AgentHalo/releases/download/v1.0.1/AgentHalo-1.0.1-x64.dmg) |

同名 `.zip` 提供相同的应用，和 `.dmg` 二选一即可。浏览器扩展继续使用 [v0.3.3](https://github.com/addsumtech/AgentHalo/releases/tag/web-bridge-v0.3.3)，无需重新安装扩展。

## 首次打开与已知限制

- 本版只提供 macOS 安装包，仍未做 Apple 公证。手动下载后如被系统阻止，请到“系统设置 → 隐私与安全性”选择“仍要打开”。
- 暂无自动更新，可重新运行上面的一键安装命令。
- 浏览器扩展目前通过“安装指引”手动加载；网页开始生成回答后，桌宠才会收到对话状态。

## 校验和

```text
95a778b0bb0da0a9fd3e4ab1f5e6ee926d6afa8e0cc3681e9d4e47e9d0c2b82a  AgentHalo-1.0.1-arm64.dmg
be17ffda546bb0c399e2a5bac36ed679fc26e2a64604e92f2d1f1ea37d493b00  AgentHalo-1.0.1-arm64.zip
9365c69e0180d9b348ee65a335d2dcef827affe6be5dd06931385798a7edb01d  AgentHalo-1.0.1-x64.dmg
c4154bd8820ddf9f5ca563018ddf4fac1a3865889ae53a60bc685cd5ff04c06d  AgentHalo-1.0.1-x64.zip
```

## 许可证

AGPL-3.0-only。基于 [Clawd on Desk](https://github.com/rullerzhou-afk/clawd-on-desk) 开发，保留上游版权和许可证。
