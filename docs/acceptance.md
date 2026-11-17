# 验收报告 — 2026-11-12

## 交付范围

独立本地 devstart-agent 项目；未修改 Backend/UI/Labs，也未写任何 DevStart 业务数据。未创建远程仓库，现有 GitHub 连接查询 devstart-agent 返回 404（不存在或不可访问，不能据此断言全局不存在）。

通过 GitHub 只读连接检查当前代码与 HEAD：

|仓库|当前 SHA|
|---|---|
|Backend|63603b749028e2c3c6502c0d61d47ca0bc6450f6|
|UI|8d0c1240deedc91b1b88139dd2c143c98e46cba6|
|Labs|11c1df3301a9b76241007629c468f28745d1c741|

Backend/UI 与指定基线相同。重点检查 TrainingService、WorkflowService.detail、ChallengeController/Service/DTO、UserController 与 Api envelope。所有实现按实际 snake_case 业务 Map 与 camelCase Challenge DTO 适配。

## 验证

最终结果：`30 passed, 1 skipped in 0.84s`；跳过的是需要凭据的真实模型测试。交付为本地目录，未建立 Git 提交，因此无 Commit SHA。

Python 3.13.5；核心与传递依赖见 requirements.lock。Agents SDK 0.6.1 / OpenAI 2.8.1 / httpx 0.28.1。SDK Loop 测试发现最新版 OpenAI 2.54.0 的 InputTokensDetails 与旧 SDK 不兼容，现已显式固定 2.8.1。pip check 通过。

pytest 覆盖训练查询、required 统计、四种阶段状态、人工 PENDING/FAIL、AUTO 隔离、已分配/未分配题目、Reviewer Staff 所有七类 Private/Hidden 字段隔离、跨训练拒绝、401/403、超时、额外工具输入、工具预算、Prompt Injection 无写能力、无成功工具结果覆盖、日志脱敏、真实 SDK 的 Mock HTTP 协议闭环、响应大小与重定向限制。

Mock 协议闭环的实际执行顺序：Mock 模型响应 → get_current_stage → 读取训练/阶段列表/阶段详情 → SDK 回传工具观察 → 第二次 Mock 模型响应 → 最终回答。这是协议单测中明确编排的模型响应，绝不代表真实模型自主选择。

## 真实模型验收：未通过 / 未执行

当前进程没有 OPENAI_API_KEY，也没有可使用的模型凭据；CLI 已验证明确报错“缺少 OPENAI_API_KEY；未执行模型推理”。opt-in 测试默认跳过。没有真实模型工具调用轨迹，不提供虚构顺序。代码测试通过不等于真实 Agent 运行通过。

配置个人模型凭据后运行 `RUN_MODEL_INTEGRATION=1 pytest -m integration -s`，该测试使用真实模型和 Mock 只读 Backend，打印实际工具顺序及脱敏审计记录。它要求模型自行调用四个工具，未预置调用序列。随后还需要使用个人 JWT 在真实测试环境执行 CLI，验证真实 Backend 权限与模型联合运行。不得将密钥或 JWT 粘贴进验收报告。

## 限制及后续

- 尚未连接真实 Spring Boot 测试环境；没有用户 JWT 或运行地址。
- OpenAI-compatible 服务提供配置入口及协议测试，尚无任何真实第三方服务兼容性通过声明。
- 工具成功后回答的忠实度仍依赖模型，需要真实场景评测；无工具成功则应用层拒绝事实回答。
- /challenges 为当前用户可访问的版本列表；在进程内按绑定 versionId 定位，再仅投影公开内容。若未来增加按 Training 的公开版本端点，可减少内存中接触 Staff DTO 的范围。
- 单轮 Stage 缓存不保证跨 HTTP 的数据库事务快照；不主动刷新或重新计算 Gate。
- 本地日志包含角色与 Training ID，部署时应设置保留与访问策略。
- Python 3.11/3.12 尚未实测；当前测试运行于 3.13.5。
- UI 嵌入方案见 architecture.md：新增受认证的 Agent 运行服务与证据展示组件，保持个人权限边界，无需改动业务生命周期。
