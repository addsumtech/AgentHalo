# 未修复的已知缺陷

来源：2026-09-14 的四路对抗性审查。审查方法是先推导这个子系统**必须**成立的不变量，再主动构造反例，而不是读代码找可疑处。所以下面每一条都附了具体触发序列。

当天已修复的不在此列（路由崩溃、偏好截断写入、UTF-8 跨包损坏、原型链键、会话清理不一致、未知配置字段被删、三处计时器泄漏、WSL PID 跨命名空间误判存活）。

---

## 1. Claude 被扣留的完成事件永远不补播

**影响**：完成动画、完成音效、Done 徽标、已读标记全部丢失，而且 recap 里记不到 `turn-complete`。卡片会额外显示五分钟「工作中」，然后被清理成 idle。

**位置**：`agenthalo/src/state.js` 的 `hardLiveWork` 分支。它把状态按住为 `working`、把事件置为 `null`，**但不安排任何定时器**。`promoteCompletion` 只有两个调用方，都是这条路径从不安排的定时器。

**触发序列**（已复现）：

1. `UserPromptSubmit`，然后 `PreToolUse`
2. `Stop` 携带 `background_tasks: [{type:"subagent"}]`，于是 hook 发出 `background_subagents_count: 1`，处置结果是 `hold`
3. 后台子代理结束 → `SubagentStop` 且 `background_subagents_count: 0`
4. 五分钟后陈旧清理把它翻成 idle

关键点在第 3 步：扣留的释放信号是 `SubagentStop`，而代码注释假设的是"之后会有一个普通 Stop 来补播"。对后台子代理来说那个 Stop 永远不会来。

**同一条路径更严重的变体**：任何注册了 cron 的会话。`session_crons.length > 0` 会让每一个 Stop 都判成 `hardLiveWork`，于是会话永远出不了 `working`。（审查者标注：这取决于 Claude 是否把已注册但空闲的 cron 也列进 `session_crons`；如果只列进行中的，这个变体退化成上面那个。）

**为什么没修**：这段是全文件防护最密的地方，`#406`、`#862`、`#952` 三个事故编号的注释都在这里，防的正是**误报完成**。修复需要在扣留时暂存 payload、在扣留解除时补播，而解除点分散在好几个分支里。没有真实的 Claude Code 后台子代理环境无法端到端验证，改错会产生假的完成庆祝——正是那些防护要防的事。

---

## 2. 未来版本的配置文件会静默丢弃所有修改

**影响**：整个会话期间用户改的每一项设置都不落盘，而 UI 全程显示成功。更糟的是带外部副作用的命令仍然执行：点了安装 Gemini，hook 真的写进 `~/.gemini/settings.json`，UI 显示"已安装"，重启后偏好里却是未安装——AgentHalo 从此不再管理也不会清理那个 hook。

**位置**：`agenthalo/src/prefs.js` 的未来版本分支返回 `locked: true` 但不带 `recovered`；`settings-controller.js` 把它当成功处理；`main.js` 的启动警告只看 `readFailure` 和 `recovered` 两个状态。

`src/i18n.js` 里根本没有对应的文案键，渲染层也没有任何地方读 `isLocked()`。用户得不到任何信号。

**触发**：回滚到 `CURRENT_VERSION` 更低的版本，或者和更新的安装共用配置目录。

**为什么没修**：需要新增七种语言的文案，以及决定"锁定状态下 UI 该长什么样"——是禁用所有开关，还是顶部挂一条持续警告。这是产品决策，不该我替你定。

---

## 3. 关于页的清理会在失败时也标记全部卸载

**影响**：hook 留在 `~/.claude/settings.json` 等文件里，而偏好声称什么都没装。之后没有任何机制会去对账，因为启动同步只处理 `integrationInstalled: true` 的 agent。用户看到错误提示，但状态已经翻过去了。

**位置**：`agenthalo/src/settings-actions.js` 的清理命令无条件返回 `status: "ok"`，于是控制器提交了那份把全部 21 个 agent 标成未安装的映射——哪怕清理抛了异常，哪怕 `summary.failed` 里有计数。

**触发**：`~/.claude/settings.json` 只读，或被别的工具占用。

**为什么没修**：改动本身小，但"部分失败"要怎么呈现需要定：是整体回滚，还是只标记成功的那些、把失败的留在已安装状态并提示用户手动处理。

---

## 4. `agents` 和 `themeOverrides` 可经 IPC 写入任意对象

**影响**：内存中的快照和磁盘不一致，而 `agent-gate` 在缺失条目时是**失败开放**的，于是所有 agent 的开关和"已安装"判定都会返回真。此时拨动任一 agent 的开关会走"已安装"分支，真的去写那个 agent 的 hook 文件。

**位置**：`settings-actions.js` 里这两个键用的是 `requirePlainObject`，而 `settings-ipc.js` 只拦截了 `tgMigration` 和四个权限自动化键。对照：`kimiQuotaCollectionEnabled` 就带了 `commandOnly: true`，正是为了这个。

**审查者的诚实标注**：现有代码没有任何路径会把 `agents` 走 `settings:update`，各个标签页用的都是 `setAgentFlag`。所以这需要渲染层出 bug 或 IPC 被误用才会触发，属于**边界缺失**而不是可直接触发的数据丢失。重启即恢复。

---

## 5. 桌宠渲染器的自愈是进程级一次性的

**位置**：`agenthalo/src/displayed-visual-projection.js` 的 `rendererReloadUsed` latch。`reset()` 会重置同一结构里其他所有计数器，唯独不重置它。

连续两次结算超时后，主进程会重载桌宠的 webContents——每次应用运行**只能发生一次**。在以周计的运行时长里，第二次独立卡死就没有恢复路径了，桌宠会永远停在一帧上。

**审查者标注为推测**：latch 本身读得很明白，但无法按需制造渲染器卡死，所以没能演示第二次。和 `reset()` 里其他计数器的不对称看起来像疏漏而非有意的防重载循环设计，但这是该由文件负责人判断的事。

---

## 审查确认没问题的地方

记下来是为了避免重复审计：hook 端的原子写（tmp+rename、`linkSync`、`wx`+rename）都正确；所有有界缓存都真的有上限（codex turns 200、DSH fence 512、hook 事件环 50、会话 20）；hook 的超时阶梯每条路径都会终止；权限气泡不泄漏窗口；所有 `innerHTML` 赋值要么是模块常量要么走了转义；IPC 订阅都是模块级注册一次。

时钟回拨在每个消费方都会让 age 变负，属于失败安全——不会提前过期。时钟前跳（睡眠唤醒）会让一轮清理同时老化所有会话，这是挂钟设计的固有限制，不是 bug。
