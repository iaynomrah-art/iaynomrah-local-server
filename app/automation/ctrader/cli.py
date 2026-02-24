import asyncio
import json
import sys
import os

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Add the project root to sys.path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from app.automation.ctrader.main import run as run_ctrader

async def main():
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Missing arguments"}))
        return

    try:
        args_str = sys.argv[1]
        args = json.loads(args_str)
        
        await run_ctrader(**args)
    except Exception as e:
        print(f"RESULT_JSON:{json.dumps({'status': 'error', 'message': str(e)})}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"RESULT_JSON:{json.dumps({'status': 'error', 'message': f'CLI Exception: {str(e)}'})}")
    finally:
        sys.stdout.flush()
