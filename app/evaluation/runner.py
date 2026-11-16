"""Run a small, fixed live benchmark. No model calls without --live."""
import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import tempfile
import os
import time

from fastapi.encoders import jsonable_encoder
from app.agents.manager import stream_agent
from app import config
from app.services.demo_policy import public_demo

TASK_FILE = Path(__file__).resolve().parents[2] / 'evaluation/tasks.json'


def tasks():
    return json.loads(TASK_FILE.read_text())


def check_result(task, result):
    execution = result.get('execution', {})
    files = {file['path'] for file in result.get('code', {}).get('files', [])}
    checks = {
        'execution_succeeded': execution.get('success') is True,
        'stdout_matches': execution.get('stdout', '').strip() == task['expected_stdout'],
        'required_files_present': set(task['required_files']).issubset(files),
    }
    return {'passed': all(checks.values()), 'checks': checks}


def summarize(rows):
    return {'tasks': len(rows), 'passed': sum(row['passed'] for row in rows),
            'success_rate': round(sum(row['passed'] for row in rows) / len(rows), 3) if rows else 0,
            'median_seconds': round(statistics.median(row['seconds'] for row in rows), 3) if rows else 0,
            'total_attempts': sum(row['attempts'] for row in rows)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Authorize real provider and Docker calls')
    parser.add_argument('--output', default='evaluation/results/latest.json')
    parser.add_argument('--ids', nargs='*')
    parser.add_argument('--pause', type=float, default=60, help='Seconds between tasks to respect free provider quotas')
    args = parser.parse_args()
    if not args.live:
        parser.error('--live is required; evaluation consumes configured model quota')
    output = Path(args.output).resolve()
    rows = []
    for task in tasks():
        if args.ids and task['id'] not in args.ids:
            continue
        if rows and args.pause > 0:
            time.sleep(min(args.pause, 60))
        started = time.perf_counter()
        result = None
        stages = []
        async def collect():
            nonlocal result
            async for item in stream_agent(task['prompt']):
                if item['event'] == 'stage': stages.append(item['data'])
                elif item['event'] == 'complete': result = jsonable_encoder(item['data']['result'])
        marker = public_demo.set(True)  # Cap Groq output and disable provider retries/dependencies.
        previous = Path.cwd()
        try:
            with tempfile.TemporaryDirectory(prefix='mini-devin-eval-') as folder:
                os.chdir(folder)
                asyncio.run(collect())
            row = {'id': task['id'], 'title': task['title'], **check_result(task, result),
                   'attempts': len(result['attempts']), 'review_approved': result['review']['success'],
                   'result': result}
        except Exception as error:
            row = {'id': task['id'], 'title': task['title'], 'passed': False,
                   'attempts': sum(item['stage']=='execute' for item in stages),
                   'error': 'provider_rate_limit' if getattr(error.__cause__, 'status_code', None)==429 else 'provider_or_execution_failure'}
        finally:
            os.chdir(previous)
            public_demo.reset(marker)
        row['seconds'] = round(time.perf_counter() - started, 3)
        rows.append(row)
        report = {'recorded_at': datetime.now(timezone.utc).isoformat(), 'provider': config.ACTIVE_LLM,
                  'model': config.GROQ_MODEL if config.ACTIVE_LLM == 'groq' else config.ACTIVE_LLM,
                  'dataset': 'evaluation/tasks.json', 'pause_between_tasks_seconds': args.pause, 'method': 'Exact stdout, successful execution and required files; reviewer approval is reported separately.',
                  'scope': 'Five small fixed tasks, one run per task; not a general coding benchmark.',
                  'summary': summarize(rows), 'cases': rows}
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + '\n')
        print(f"{task['id']}: {'PASS' if row['passed'] else 'FAIL'} ({row['seconds']}s)", flush=True)
    print(json.dumps(summarize(rows)), flush=True)


if __name__ == '__main__':
    main()
