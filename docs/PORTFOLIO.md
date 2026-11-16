# Portfolio and interview guide

## A concise project description

Mini-Devin is an observable Python coding workspace: a request moves through
planning, generation, bounded Docker execution and review, with a limited repair
loop. It includes inspectable attempts, diffs, stage timings, downloads, persistent
private history and a quota-controlled public portfolio demo.

## Resume bullet

Built and deployed an AI-assisted Python development workspace with LangGraph,
FastAPI, React and Docker; implemented streamed stage updates, bounded execution,
inspectable code-repair attempts, private run history and a public demo with
persistent usage limits.

Use the committed evaluation report for exact task counts and timing if adding a
metric. A five-task smoke evaluation is not an accuracy claim for arbitrary coding
problems. Do not describe this as a production multi-tenant service or claim
unmeasured token-cost savings or user adoption.

## A 60-second demonstration

1. Open the public URL and choose the recorded repair example. No token needed.
2. Show the actual failed assertion in attempt 1.
3. Select attempt 2, open Changes and explain the correction.
4. Inspect the plan, copy a source file and download the project ZIP.
5. Explain that live examples use real model requests and Docker; recordings stay
   available when free-provider quotas are exhausted.
6. Point to the independently checked benchmark and passing CI run on GitHub.

## Decisions to be ready to explain

- Why model review is separate from executable correctness checks.
- Why state-machine orchestration uses bounded retries.
- How SSE differs from individual model-token streaming and what disconnect means.
- Why Docker resource controls, read-only source and no runtime network matter.
- Why SQLite quota reservation is transactional and survives process restarts.
- Why public example IDs cannot become arbitrary owner API requests.
- How source path validation also matters for downloaded ZIP archives.
- Why a single worker and dedicated host fit this project's current budget/scope.
- What would change for tenant isolation, distributed execution and durable jobs.

The project was developed with AI assistance. Be able to explain, modify and debug
these mechanisms yourself; that is stronger evidence than describing it as an
unlimited autonomous software engineer.
