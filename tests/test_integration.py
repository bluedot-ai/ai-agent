"""Real model, mocked read-only backend. Never a scripted model response."""
import os
import pytest
from devstart_agent.config import Config
from devstart_agent.agent import run_agent
from test_tools import ctx

@pytest.mark.integration
async def test_real_tool_calling(ctx):
    if os.getenv('RUN_MODEL_INTEGRATION')!='1': pytest.skip('opt-in real model credentials required')
    answer=await run_agent(ctx,'请核实当前训练、阶段阻塞、人工门禁以及题目的公开要求。',Config.load())
    trace=[e['tool'] for e in ctx.audit.events if e['kind']=='tool']
    print('\nActual autonomous tool sequence:',trace)
    print(ctx.audit.dump())
    assert ctx.successful=={'get_training','get_current_stage','get_pending_gates','get_challenge'}
    assert answer
