# 架构

CLI → 可信 AgentContext(training_id, api_client) → Agents SDK 单 Agent/Runner → 四个 FunctionTool → 固定 GET API → Spring Boot Access → MySQL。

模型只看到问题、系统指令、公开投影后的工具结果，不看到 Context 对象、Token、原始响应或本地日志。所有工具都是零参数；本地校验参数必须为空对象，模型不能选择 Training、Stage 或 URL。Stage ID 仅来自绑定训练的 stages 列表，Detail 再校验归属。启动前检查 users/me 与训练读取权限，所有后续请求仍使用同一用户 JWT。

- get_training：投影 status、currentStage、reviewerName、challengeSelected。
- get_current_stage：按 training.current_stage_code 匹配阶段，保留后端状态，仅统计 required_flag=true 的 checkpoint；输出未完成项与 Gate 状态。
- get_pending_gates：复用本次 Run 的 Stage 快照，仅聚合 MANUAL 的 PENDING/FAIL。waitingForReviewer 表示活动阶段必需检查点完成且存在必需人工待审项，不保证这是唯一阻塞。AUTO 不算导师待办。
- get_challenge：Training 提供 version ID；现有 /challenges 列表包含用户可访问版本，用 versionId 精确匹配。Reviewer/Admin Staff DTO 仅解包 publicContent，随后再次按 12 个允许字段投影，不返回 ID、tags、Private 或 Hidden。列表原始数据仅短暂驻留 API 层，不进模型或日志。

不调用 reviewer/pending-gates。所有业务操作固定 GET；无数据库连接、状态写入、生命周期逻辑修改。Stage Detail 当前实现不会触发 evaluateGates。Stage 快照限单轮 Run，下一次启动重新读取，无法提供事务一致的跨请求快照。

Prompt 将业务文本视为不可信数据，且能力边界没有任何写工具。没有成功工具结果时应用层覆盖模型输出为无法核实；成功读取后的自然语言仍需评估事实忠实度，不能将 Prompt 约束视为形式化证明。

外部 SDK tracing 禁用。本地日志仅白名单元数据；不存输入、输出、工具参数、响应体、异常原文。SDK 依赖中包含 MCP 包是上游传递依赖，本项目不配置或使用 MCP。

未来 UI：部署同一服务为受认证的流式运行入口，服务端从当前用户与已授权 Training 绑定 Context，逐请求转发个人 JWT；增加取消、运行配额、审计保留策略及 UI 证据面板。不需要更改 Workflow、Gate、Checkpoint、Migration。

SDK 参考：https://developers.openai.com/api/docs/guides/tools
