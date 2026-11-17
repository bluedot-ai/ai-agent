# DevStart Training Agent POC 0.1

独立 Python 3.11+ 只读 CLI。四个零参数 FunctionTool 由模型自主选择，Agents SDK Runner 处理观察及后续调用；无预置工具调用序列。

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.lock
pip install --no-deps -e .
# .env.example 仅是配置示例，本程序不会自动加载 .env
export DEVSTART_BASE_URL=http://localhost:8080
export OPENAI_API_KEY='自己的模型密钥'
export AGENT_MODEL=gpt-4.1-mini
python -m devstart_agent.cli --training-id 1 --debug
pytest -q
RUN_MODEL_INTEGRATION=1 pytest -m integration -s
```

CLI 使用 getpass 读取个人 JWT，不写盘，不传模型。输入单轮问题后退出。`--log-file` 默认写入当前目录 devstart-agent.jsonl，仅记录脱敏元数据。不要在终端命令行传 JWT。

官方模型默认 Responses。兼容服务设置 `OPENAI_BASE_URL`、`AGENT_MODEL`、`AGENT_MODEL_API=chat_completions`。兼容性必须逐服务运行 opt-in 测试，不能仅凭 API 格式断言兼容。模型不可用时退出码 1，不生成替代推理结果。

HTTP 超时 10 秒、响应 256 KiB、禁止重定向，远程 Backend 必须 HTTPS。Run 最多 6 轮、8 次工具执行、120 秒；模型请求 30 秒，不重试。外部 Trace 禁用。

参见 docs/architecture.md 与 docs/acceptance.md。
