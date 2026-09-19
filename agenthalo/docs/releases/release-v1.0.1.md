# AgentHalo 1.0.1

这次更新让设置入口、角色导入和浏览器扩展安装更清楚。

## 更新内容

- 新安装默认显示 Dock 图标，点击即可打开设置主界面；已有用户的显示偏好保持不变。
- 桌面伙伴统一为“导入角色包”，自动识别 AgentHalo 和 Codex Pet 格式，入口移至角色列表下方。
- 统一设置页与弹窗的文字层级：正文、标签和按钮使用常规字重，标题适度强调。
- 连接检查改为简洁列表，减少正常状态的重复装饰，突出主要操作。
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
fb4ab2e9d2bac714035baaba4437df73dfdabfcfe356bed91f21e9c7ad98814c  AgentHalo-1.0.1-arm64.dmg
39ab0d87898085388c7df535eff1653d0924501206101dd2d69d972e88765d38  AgentHalo-1.0.1-arm64.zip
c5f8d903680657bc395bce064f56df03b53cd8e5c27c9c6df28087d22bbf0059  AgentHalo-1.0.1-x64.dmg
319d18908da9a068e99e14419b9c135fe362a070e810a5a6a8f25bf7b6353bfe  AgentHalo-1.0.1-x64.zip
```

## 许可证

AGPL-3.0-only。基于 [Clawd on Desk](https://github.com/rullerzhou-afk/clawd-on-desk) 开发，保留上游版权和许可证。
