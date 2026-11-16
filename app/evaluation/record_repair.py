"""Record a seeded failure repaired by the real configured model and Docker."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import os
import time
from fastapi.encoders import jsonable_encoder
from app.agents.coder import rewrite_code
from app.agents.reviewer import review_code
from app.executor.runner import execute_code
from app.models.schemas import Plan, CodeResponse, GeneratedFile, ReviewResult
from app.services.demo_policy import public_demo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    if not args.live:
        parser.error('--live is required')
    output = Path(args.output).resolve()
    prompt = 'Fix average so average([1,2]) equals 1.5 and average([]) equals 0.0. Include both assertions and print exactly Average: 1.5. No dependencies.'
    plan = Plan(goal='Repair a failing average calculation', features=['Fractional averages', 'Empty-list handling', 'Regression assertions'], files=['main.py'], technologies=['Python standard library'], steps=['Reproduce the assertion failure', 'Repair with model feedback', 'Execute and review the correction'])
    broken = CodeResponse(files=[GeneratedFile(path='main.py', content='def average(values):\n    return sum(values) // len(values)\n\nassert average([1, 2]) == 1.5\nassert average([]) == 0.0\nprint(f"Average: {average([1, 2])}")\n')])
    previous = Path.cwd()
    marker = public_demo.set(True)
    try:
        with tempfile.TemporaryDirectory(prefix='mini-devin-repair-') as folder:
            os.chdir(folder)
            failed = execute_code(broken)
            assert not failed.success and 'AssertionError' in failed.stderr
            feedback = ReviewResult(success=False, feedback='Seeded regression: integer division discards fractions. Preserve fractional averages and handle empty lists. Both assertions must pass.', failure_source='code')
            started = time.perf_counter()
            fixed = rewrite_code(plan, broken, feedback.feedback)
            generate_ms = round((time.perf_counter() - started) * 1000)
            execution = execute_code(fixed)
            assert execution.success and execution.stdout.strip() == 'Average: 1.5', 'Independent output check failed'
            started = time.perf_counter()
            review = review_code(plan, fixed, execution, prompt)
            review_ms = round((time.perf_counter() - started) * 1000)
            result = {'plan': plan, 'code': fixed, 'execution': execution, 'review': review,
                      'attempts': [{'attempt': 1, 'code': broken, 'execution': failed, 'review': feedback, 'success': False},
                                   {'attempt': 2, 'code': fixed, 'execution': execution, 'review': review, 'success': execution.success and review.success}],
                      'timings': [{'stage': 'execute', 'attempt': 1, 'duration_ms': round(failed.execution_time * 1000)},
                                  {'stage': 'generate', 'attempt': 2, 'duration_ms': generate_ms},
                                  {'stage': 'execute', 'attempt': 2, 'duration_ms': round(execution.execution_time * 1000)},
                                  {'stage': 'review', 'attempt': 2, 'duration_ms': review_ms}]}
            recording = {'id': 'repair', 'title': plan.goal, 'recorded_at': datetime.now(timezone.utc).isoformat(),
                         'provenance': 'Recorded demonstration: a deliberately seeded bug, real model rewrite, actual Docker executions, and model review. Not an unseeded success-rate measurement.',
                         'result': jsonable_encoder(result)}
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(recording, indent=2) + '\n')
            print('Recorded seeded failure, real model repair, exact output and Docker verification.', flush=True)
    finally:
        os.chdir(previous)
        public_demo.reset(marker)


if __name__ == '__main__':
    main()
