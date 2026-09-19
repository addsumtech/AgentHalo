# AgentHalo Web Bridge

把 Claude、ChatGPT、Gemini 网页对话的生成状态同步给 AgentHalo 桌宠。

[English](README.en.md) · 简体中文

[下载扩展包 v0.3.3](https://github.com/addsumtech/AgentHalo/releases/download/web-bridge-v0.3.3/AgentHalo-Web-Bridge.zip)

## 首次安装（macOS）

需要已安装的 AgentHalo、Node.js 22 或更新版本，以及 Chrome 或 Edge。

1. 下载 `AgentHalo-Web-Bridge.zip`，解压到任意临时目录。安装脚本会把扩展复制到固定的应用数据目录。
2. 至少启动一次 AgentHalo，然后从桌宠菜单选择「退出」。
3. 在终端切换到解压后的 `AgentHalo-Web-Bridge` 目录，运行：

   ```sh
   node scripts/register.js
   ```

   脚本会备份 AgentHalo 偏好，注册三个网页应用，生成仅供本机使用的配置，并将扩展安装到 `~/Library/Application Support/AgentHalo/WebBridge/extension`。已有网页应用的启用和通知偏好会保留。如果 AgentHalo 仍在运行，脚本会停止并提示退出。

4. 重新打开 AgentHalo。
5. Chrome 打开 `chrome://extensions`，Edge 打开 `edge://extensions`；启用「开发者模式」，选择「加载已解压的扩展程序」，选中 `~/Library/Application Support/AgentHalo/WebBridge/extension` 文件夹。文件选择器中可按 `⌘⇧G`，粘贴此路径并回车。
6. 刷新已经打开的聊天页面。发送消息后，可从桌宠菜单的「任务列表」查看对应会话。

下载无需 GitHub 仓库访问权限。安装包不含本机注册 ID、偏好、凭据或运行日志。

## 更新

当前扩展版本为 **0.3.3**。退出 AgentHalo，在新版解压目录运行 `node scripts/register.js`，脚本会保留已安装的本机配置并更新固定目录中的文件。然后重新打开 AgentHalo，在浏览器扩展管理页点「重新加载」，再刷新聊天页面。更换电脑或用户时重新执行注册脚本。若安装目录变动，需移除旧扩展并从新目录重新加载。

## 状态与边界

- 生成开始显示思考，持续生成超过 2.5 秒切到工作；回复完成显示等待，关闭标签或切换会话时清理旧卡片。
- 每个标签页独立识别，复制标签页不会共用会话；后台服务重启后保留对应关系。
- macOS 点击任务卡片时优先定位已有标签，确认不存在时才打开链接。
- 网页接入仅同步状态，不处理权限审批；浏览器扩展会读取当前对话 URL、标题和生成状态。
- 自动探测本机 AgentHalo 的 23333–23337 端口。无法连接时，先检查 AgentHalo 是否运行，再查看扩展管理页中的 Service Worker 日志。
- Claude Code 网页模式和 Codex 云端任务不在网页扩展的识别范围内；本地 Codex 由 AgentHalo 自身接入。
- 保留千问网页检测代码，但首次安装脚本不注册千问网页，本轮未做其实机验证。千问桌面客户端专用观察器已移除；Qwen Code、QwenWork 仍使用 AgentHalo 原生 hook 接入。
- 站点改版可能影响状态识别；检测逻辑位于 `extension/content.js`。本轮验证扩展状态机和安装包，未重新提交三个站点的真实对话。

## 开发打包

在 macOS 或装有 `zip` 的环境运行：

```sh
node scripts/package-extension.js
node --test test/*.test.js
```

打包脚本只收录明确列出的运行文件，并用空白模板生成分发用 `config.js`。

## License

AGPL-3.0-only，详见安装包的 `LICENSE` 与 `NOTICE.md`。扩展运行源代码包含在下载包中。
