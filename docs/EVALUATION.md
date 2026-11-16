# Evaluation methodology

The fixed dataset in evaluation/tasks.json covers a sequence, CSV data quality,
a multi-file import, a fractional-average fix and grouped totals. Each task has an
independent expected stdout and required file list. A task passes only if actual
execution succeeds, stdout matches (ignoring surrounding whitespace) and all
required files exist. A model saying the result is correct cannot override a
failed output check.

## Reproduce

Start Docker, configure a provider privately, then explicitly authorize model calls:

```sh
.venv/bin/python -m app.evaluation.runner --live --output evaluation/results/latest.json
```

The runner uses a temporary source workspace, performs at most three execution
attempts per task and does not archive results into owner history. Groq calls use
bounded output and no provider retries in this mode. Results include timestamps,
provider/model, wall time, execution attempts, separate review approval and each
output/file check. Failures remain in the denominator. Review source before
publishing recordings; never substitute a private prompt or history export.

The report is a small reproducible smoke benchmark: five fixed tasks, one run per
task. It is not a statistically representative accuracy claim, a standard external
coding benchmark, or a guarantee about arbitrary generated programs. Completion
times include model, sandbox, review and retry work, and depend on provider load.
No model-token usage or monetary estimate is fabricated from execution timing.

## Repair walkthrough

```sh
.venv/bin/python -m app.evaluation.record_repair --live --output repair.json
```

This intentionally supplies a seeded integer-division bug. Docker first reproduces
an assertion failure, the configured model rewrites it, Docker runs the repaired
version and a reviewer examines it. The displayed code diff compares those actual
sources. This teaching demonstration is not counted as an unseeded benchmark win.

## Automated checks

GitHub Actions runs locked Python/Node dependencies, offline backend tests,
frontend component/SSE/ZIP tests, a production build and real Docker integration
on a standard Linux runner. It has read-only repository permission, immutable
Action references and no AWS/model credentials. Live provider evaluation is never
triggered automatically by a pull request.

## Recorded runs — November 16, 2026

The paced run passed **5/5 fixed tasks** with a median completion time of **4.756
seconds** and five completed execution attempts. Tasks were spaced 60 seconds
apart; the median excludes that deliberate inter-task wait. See
[the complete report](../evaluation/results/latest.json).

The earlier unpaced trial passed **2/5** and encountered provider token-per-minute
throttling. Its failures remain visible in [the original trial](../evaluation/results/unpaced-trial.json).
This operational finding motivated a shared cooldown on public live runs and the
always-available recorded walkthroughs. It is not hidden by the paced result.

The original unpaced launcher reports completed-result attempts only; a task that
failed before final review may have executed code without a completed result. The
current runner also counts execution-stage events in failed tasks. Initial local
launcher permission errors were corrected before these two recorded trials; they
are not claims about generated-program correctness. Some earlier execution
diagnostics reflect that launcher's Docker home-directory warning, not a nonzero
program exit. Raw stderr is retained for transparency.
