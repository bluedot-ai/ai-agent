import argparse
import asyncio
import getpass
import sys
from .config import Config
from .api_client import ApiClient, BackendError
from .context import AgentContext
from .observability import Audit
from .agent import run_agent

async def run(args):
    config = Config.load()
    token = getpass.getpass("请输入自己的 JWT（不保存）：")
    audit = Audit(args.training_id)
    client = ApiClient(config.backend, token, args.training_id, audit)
    try:
        context = AgentContext(args.training_id, client, audit)
        await context.preflight()
        question = input("问题：")
        print(await run_agent(context, question, config))
    finally:
        await client.close()
        if not any(e["kind"] == "run" for e in audit.events):
            audit.record("run", status="error", model_calls=0)
        audit.save(args.log_file)
        if args.debug: print(audit.dump(), file=sys.stderr)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--training-id", required=True, type=int)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--log-file", default="devstart-agent.jsonl")
    args = parser.parse_args()
    if args.training_id <= 0: parser.error("training-id 必须为正整数")
    try: asyncio.run(run(args))
    except BackendError as e:
        print("API/权限错误：" + e.code, file=sys.stderr)
        raise SystemExit(1)
    except ValueError as e:
        print("配置错误：" + str(e), file=sys.stderr)
        raise SystemExit(1)
    except (KeyboardInterrupt, EOFError): raise SystemExit(130)
    except Exception:
        print("模型或运行错误；未完成推理。请检查模型配置和网络。", file=sys.stderr)
        raise SystemExit(1)

if __name__ == "__main__": main()
