# Where to find each implemented feature

| Feature | Interface / implementation | Access |
|---|---|---|
| Create your own Python program | Root studio, Your task → Build my project; /demo/stream custom mode | Public quota |
| Full project generation + repair retries | /workspace; /api/chat/stream | Workspace token |
| Generated files and folders | Project files pane; app/executor/workspace.py | Current result |
| Add / remove / edit source | Add file, Edit files, Reset project edits | Browser copy |
| Run edited files | Run edited project; /api/projects/execute | Workspace token |
| Source diffs | Changes tab, select a later attempt | Current result |
| Execution stdout/stderr | Execution console | Current result |
| Timing evidence | Workflow + Inspect stage timings | Current result |
| Download source | Download ZIP | Current result |
| GitHub preview and JSON handoff | Export to GitHub | Current result |
| Publish branch / draft PR | app.tools.github_export --apply --create-pr | Local repo-scoped credential |
| Restore completed runs | Full workspace → Load saved runs | Workspace token |
| Context retrieval | Full workspace → Use project references; RAG_ROOT | Workspace token + configured corpus |
| Multiple provider adapters | .env; app/services/llm | Local/server configuration |
| Docker sandbox and bounded execution | app/executor | Backend |
| Architecture, evaluations, recordings | Engineering section and docs | Public |

The browser file pane represents the generated project, not a general-purpose
host filesystem explorer. No arbitrary server path is exposed. GitHub publication
is deliberately separate from generation and requires explicit CLI action.
