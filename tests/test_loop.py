import json
import httpx
import pytest
from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel
from devstart_agent.agent import run_agent
from test_tools import ctx

async def test_sdk_loop_with_mock_provider(ctx):
    """SDK protocol regression only; this is NOT a real autonomous model test."""
    calls=[]
    async def handler(request):
        payload=json.loads(request.content)
        calls.append(payload)
        if len(calls)==1:
            msg={'role':'assistant','content':None,'tool_calls':[{'id':'c1','type':'function','function':{'name':'get_current_stage','arguments':'{}'}}]}
        else:
            assert any(x['role']=='tool' for x in payload['messages'])
            msg={'role':'assistant','content':'必需检查点未完成，请由学员补齐。'}
        return httpx.Response(200,json={'id':'mock','object':'chat.completion','created':1,'model':'mock','choices':[{'index':0,'finish_reason':'tool_calls' if len(calls)==1 else 'stop','message':msg}],'usage':{'prompt_tokens':10,'completion_tokens':5,'total_tokens':15}})
    async with AsyncOpenAI(api_key='fake-test-key',http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler))) as client:
        answer=await run_agent(ctx,'为什么不能进入下一阶段？',None,model=OpenAIChatCompletionsModel(model='mock',openai_client=client))
    assert len(calls)==2 and ctx.successful=={'get_current_stage'}
    assert '必需' in answer
    assert 'fake-test-key' not in ctx.audit.dump()

async def test_sdk_no_tool_result_is_blocked(ctx):
    async def handler(request):
        return httpx.Response(200,json={'id':'mock','object':'chat.completion','created':1,'model':'mock','choices':[{'index':0,'finish_reason':'stop','message':{'role':'assistant','content':'训练已完成'}}]})
    async with AsyncOpenAI(api_key='fake',http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler))) as client:
        answer=await run_agent(ctx,'训练状态？',None,model=OpenAIChatCompletionsModel(model='mock',openai_client=client))
    assert '无法核实' in answer and '训练已完成' not in answer
