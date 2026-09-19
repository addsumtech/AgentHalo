# agenthalo

一条命令装好 [AgentHalo](https://github.com/addsumtech/AgentHalo)：跟着 AI 任务状态动的 macOS 桌面伙伴。

```bash
npx agenthalo
```

装完会自动打开，桌宠在菜单栏。接着到「设置 → 连接应用」给你在用的 AI 工具装上 hook。

## 它做了什么

1. 识别芯片（Apple Silicon / Intel），选对应的包。
2. 从对应版本的 GitHub release 下载 zip。
3. 核对 SHA-256，和本包内固定的校验和比对。
4. 用 `ditto` 解压安装到 `/Applications`，并启动。

安装到别处：

```bash
npx agenthalo --dir ~/Applications
```

`/Applications` 不可写时会自动退到 `~/Applications`，全程不需要 sudo。

## 为什么用 npx 而不是下 dmg

macOS 的 Gatekeeper 只拦带 `com.apple.quarantine` 属性的文件，而这个属性是**下载文件的那个程序**打上去的：浏览器会打，`curl` 和 Node 不打。

所以浏览器下载的 dmg 会触发「无法验证开发者」，需要手动去「系统设置 → 隐私与安全性」放行；从这里装则不会，装完直接能开。两种方式拿到的是同一个应用。

## 要求

- macOS，Node 18 以上。
- 只有 macOS 包。其它平台见 [Releases](https://github.com/addsumtech/AgentHalo/releases)。

## 许可证

AGPL-3.0-only，与 AgentHalo 本体一致。AgentHalo 基于 [Clawd on Desk](https://github.com/rullerzhou-afk/clawd-on-desk) 开发，上游版权与许可证均已保留。
