from agents import RunHooks, Agent, Runner, RunConfig, ModelSettings, OpenAIChatCompletionsModel, OpenAIResponsesModel, set_tracing_disabled
from openai import AsyncOpenAI
from .prompts import SYSTEM
from .tools import TOOLS

UNVERIFIED = "无法核实训练事实：本次没有成功读取工具结果，请检查 API、权限或重试。"

def verified_output(ctx, output):
    return output if ctx.successful else UNVERIFIED

async def run_agent(ctx, question, config, model=None):
    set_tracing_disabled(True)
    client = None
    model_calls = 0
    class Hooks(RunHooks):
        async def on_llm_start(self, context, agent, system_prompt, input_items):
            nonlocal model_calls
            model_calls += 1
            ctx.audit.record("model", model_calls=model_calls, status="started")
    try:
        await ctx.preflight()
        if model is None:
            client = AsyncOpenAI(api_key=config.key, base_url=config.base_url, timeout=30, max_retries=0)
            adapter = OpenAIChatCompletionsModel if config.api == "chat_completions" else OpenAIResponsesModel
            model = adapter(model=config.model, openai_client=client)
        agent = Agent(name="DevStart Training", instructions=SYSTEM, tools=TOOLS, model=model,
                      model_settings=ModelSettings(parallel_tool_calls=False))
        import asyncio
        result = await asyncio.wait_for(Runner.run(agent, question, context=ctx, max_turns=6,
            hooks=Hooks(), run_config=RunConfig(tracing_disabled=True)), timeout=120)
        usage = result.context_wrapper.usage
        ctx.audit.record("run", status="success" if ctx.successful else "unverified", model_calls=usage.requests,
                         input_tokens=usage.input_tokens, output_tokens=usage.output_tokens)
        summary = "、".join(e["tool"] for e in ctx.audit.events if e["kind"] == "tool") or "无"
        return verified_output(ctx, str(result.final_output)) + "\n本次工具：" + summary
    except Exception:
        ctx.audit.record("run", status="error", model_calls=model_calls)
        raise
    finally:
        if client: await client.close()
