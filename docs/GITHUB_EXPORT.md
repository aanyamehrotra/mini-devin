# Preview-first GitHub project export

This is a local command-line integration for exporting reviewed generated files.
It is separate from the agent loop: generation never publishes automatically.
There is no unauthenticated write endpoint, browser token field or OAuth UI.

## Prepare input and repository scope

Save the normal `/chat` response as result.json, or save a CodeResponse object
with a files list. Review the actual file contents and execution/review outcomes
before export. The exporter accepts files even if execution was not verified;
export itself does not certify code correctness, security or tests.

Set `GITHUB_EXPORT_REPO` in the command environment to one allowed owner/repository.
The CLI --repo must match it. This command reads process environment variables;
it does not automatically load the backend's .env file.

```sh
export GITHUB_EXPORT_REPO=your-owner/your-repo
.venv/bin/python -m app.tools.github_export \
  --result result.json --repo your-owner/your-repo \
  --base main --title 'Add generated Python project'
```

Without --apply, the command is an offline preview. It does not require a token,
contact GitHub, create objects or mutate files. Output includes the destination
branch/folder and file hashes/sizes, but omits source content. Inspect result.json
itself to review content. Each invocation gets a new random branch/folder ID, so
a subsequent --apply invocation has a different ID from a prior preview.

## Explicit publication

Provide `GITHUB_EXPORT_TOKEN` through a secure process environment. Use a
fine-grained GitHub token restricted to the configured repository with Contents
read/write, plus Pull requests write only if requesting a PR. Do not put a token
in CLI arguments, result JSON, frontend source, generated files or commits.

```sh
.venv/bin/python -m app.tools.github_export \
  --result result.json --repo your-owner/your-repo \
  --base main --title 'Add generated Python project' --apply --create-pr
```

--apply creates a commit and NEW `mini-devin/export-<uuid>` branch. All exported
files live under NEW `generated/<uuid>/`, rather than replacing app/root files.
The Git tree uses the base tree and base commit parent, preserving existing files.
The tool requires the export directory lookup to return 404 before creating new
objects. It never PATCHes an existing ref, force-pushes, deletes files, merges a PR
or updates the base branch. --create-pr requires --apply and opens a draft PR.

## Limits and failure handling

- Requires 1–100 files, at most 1 MiB total UTF-8 content, and bounded input JSON.
- Rejects traversal, absolute/Windows paths, duplicate paths, file/directory
  conflicts, .git metadata, and .env variants except .env.example. This is NOT a
  general secret scanner: secrets embedded in ordinary files can still be published.
- Supports GitHub.com only. Requests use HTTPS, a 20-second per-request timeout,
  no redirects, no ambient netrc/proxy configuration, and no automatic write retries.
- Only standard file blobs are created. No symlinks, submodules or executable modes.
- If PR creation fails after branch creation, output preserves branch/commit/compare
  information with a warning. Create the PR from that branch rather than re-exporting.
- If branch creation is ambiguous, the error includes branch/commit recovery fields.
  Check GitHub before retrying: a timed-out write might have reached the server.
  Other CLI failures return a sanitized error and nonzero exit status.
- Git objects may remain unreferenced when a later step fails. There is no automatic
  remote rollback or cleanup, and new-branch creation may trigger repository actions.
- Empty repositories, OAuth/account linking, editing existing repo files, UI export,
  idempotency across reruns and automatic pull-request merging are not implemented.

## Validation

The offline suite uses mocked GitHub calls. It verifies repository scoping, safe
preview defaults, path/size limits, base-tree/parent preservation, new-ref-only
writes, draft PRs, partial-failure recovery and sanitized bounded transport.
No live generated-project export/PR was created during this milestone. Actual
GitHub permissions/branch rules and behavior require a deliberately chosen test
repository. Routine development commits pushed to Mini-Devin use the pre-existing
Git access and do not verify this product's token-based export integration.

References: [Git trees](https://docs.github.com/en/rest/git/trees),
[Git references](https://docs.github.com/en/rest/git/refs),
[pull requests](https://docs.github.com/en/rest/pulls/pulls).
