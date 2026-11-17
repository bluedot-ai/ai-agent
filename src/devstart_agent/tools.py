import json
import time
from agents import RunContextWrapper, function_tool
from .context import AgentContext
from .api_client import BackendError
from .schemas import project, public_challenge

async def training(c):
    t = await c.api_client.training()
    if t["id"] != c.training_id: raise BackendError("SCOPE_MISMATCH")
    return t

async def current(c):
    if c.stage_cache is not None: return c.stage_cache
    t = await training(c)
    stages = await c.api_client.stages()
    rows = [s for s in stages if s["code"] == t.get("current_stage_code")]
    if len(rows) != 1: raise BackendError("CURRENT_STAGE_UNAVAILABLE")
    s = await c.api_client.stage(rows[0]["id"])
    if s["code"] != t["current_stage_code"]: raise BackendError("SCOPE_MISMATCH")
    cps = [project(x, ("code", "name", "completed")) for x in s["checkpoints"] if x.get("required_flag") is True or x.get("required_flag") == 1]
    gates = [project(x, ("code", "type", "status", "required_flag")) for x in s["gates"]]
    c.stage_cache = dict(code=s["code"], name=s["name"], status=s["status"],
        requiredCount=len(cps), completedCount=sum(x["completed"] is True or x["completed"] == 1 for x in cps),
        unfinished=[x for x in cps if not x["completed"]], gates=gates,
        reviewerName=t.get("reviewer_name"))
    return c.stage_cache

async def execute(c, name):
    started = time.monotonic()
    c.calls += 1
    status = "error"
    try:
        if c.calls > 8: raise BackendError("TOOL_LIMIT")
        if name == "get_training":
            t = await training(c)
            result = dict(status=t["status"], currentStage=t.get("current_stage_code"),
                reviewerName=t.get("reviewer_name"), challengeSelected=t.get("challenge_version_id") is not None)
        elif name == "get_current_stage": result = await current(c)
        elif name == "get_pending_gates":
            s = await current(c)
            manual = [g for g in s["gates"] if g["type"] == "MANUAL"]
            pending = [g for g in manual if g["status"] == "PENDING"]
            failed = [g for g in manual if g["status"] == "FAIL"]
            result = dict(pending=pending, failed=failed, reviewerName=s["reviewerName"],
                waitingForReviewer=s["status"] in {"IN_PROGRESS", "BLOCKED"} and not s["unfinished"] and any(g["required_flag"] for g in pending))
        elif name == "get_challenge":
            t = await training(c)
            vid = t.get("challenge_version_id")
            if vid is None: result = {"status":"CHALLENGE_NOT_SELECTED"}
            else:
                rows = await c.api_client.challenges()
                matches = [x for x in rows if x.get("publicContent", x).get("versionId") == vid]
                if len(matches) != 1: raise BackendError("CHALLENGE_VERSION_UNAVAILABLE")
                result = public_challenge(matches[0])
        else: raise BackendError("UNKNOWN_TOOL")
        c.successful.add(name)
        status = "success"
        return json.dumps(result, ensure_ascii=False)
    except BackendError as e:
        return json.dumps({"error":e.code})
    except (KeyError, TypeError, ValueError):
        return json.dumps({"error":"BACKEND_SCHEMA_ERROR"})
    finally:
        c.audit.record("tool", tool=name, status=status, elapsed_ms=round((time.monotonic()-started)*1000))

@function_tool(failure_error_function=None)
async def get_training(ctx: RunContextWrapper[AgentContext]) -> str:
    """查询已绑定训练的状态、当前阶段、导师和抽题情况。无参数。"""
    return await execute(ctx.context, "get_training")

@function_tool(failure_error_function=None)
async def get_current_stage(ctx: RunContextWrapper[AgentContext]) -> str:
    """查询已绑定训练当前阶段、必需检查点未完成项和门禁状态。无参数。"""
    return await execute(ctx.context, "get_current_stage")

@function_tool(failure_error_function=None)
async def get_pending_gates(ctx: RunContextWrapper[AgentContext]) -> str:
    """查询当前阶段人工门禁 PENDING、FAIL 和是否等待导师。无参数。"""
    return await execute(ctx.context, "get_pending_gates")

@function_tool(failure_error_function=None)
async def get_challenge(ctx: RunContextWrapper[AgentContext]) -> str:
    """查询绑定训练已分配题目的公开内容；绝不返回私有评分信息。无参数。"""
    return await execute(ctx.context, "get_challenge")

TOOLS = [get_training, get_current_stage, get_pending_gates, get_challenge]

# Provider-side strict schemas are insufficient: reject unexpected arguments locally too.
for _tool in TOOLS:
    _invoke = _tool.on_invoke_tool
    def strict_invoke(original):
        async def invoke(ctx, arguments):
            if json.loads(arguments) != {}:
                raise BackendError("INVALID_TOOL_INPUT")
            return await original(ctx, arguments)
        return invoke
    _tool.on_invoke_tool = strict_invoke(_invoke)
