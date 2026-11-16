import { useEffect, useState } from 'react';
import { projectZip, downloadJson } from './project.js';

export function githubHandoff(files, repository, base = 'main') {
  if (!/^[A-Za-z0-9][A-Za-z0-9-]*\/[A-Za-z0-9][A-Za-z0-9_.-]*$/.test(repository))
    throw new Error('Enter a repository as owner/name.');
  if (
    !/^[A-Za-z0-9][A-Za-z0-9._/-]{0,199}$/.test(base) ||
    ['..', '//', '@{'].some((part) => base.includes(part)) ||
    /[/.]$|\.lock$/.test(base)
  )
    throw new Error('Enter a valid base branch.');
  projectZip(files);
  for (const file of files)
    if (
      file.path
        .split(/[\\/]/)
        .some(
          (part) =>
            part.toLowerCase() === '.git' ||
            (/^\.env(?:\.|$)/i.test(part) && part.toLowerCase() !== '.env.example')
        )
    )
      throw new Error('Environment secrets and Git metadata cannot be exported.');
  const command = `export GITHUB_EXPORT_REPO='${repository}'\n.venv/bin/python -m app.tools.github_export \\\n  --result mini-devin-result.json --repo '${repository}' \\\n  --base '${base}' --title 'Add generated Python project'`;
  return {
    repository,
    base,
    command,
    files: files.map((file) => ({
      path: file.path,
      bytes: new TextEncoder().encode(file.content).length,
    })),
  };
}

export default function GitHubPanel({ files }) {
  const [repo, setRepo] = useState('');
  const [base, setBase] = useState('main');
  const [plan, setPlan] = useState(null);
  const [message, setMessage] = useState('');
  const fileSignature = JSON.stringify(files);
  useEffect(() => setPlan(null), [fileSignature]);
  function preview(event) {
    event.preventDefault();
    try {
      setPlan(githubHandoff(files, repo.trim(), base.trim()));
      setMessage('');
    } catch (error) {
      setMessage(error.message);
      setPlan(null);
    }
  }
  return (
    <section className="github-handoff" aria-label="GitHub export">
      <div className="section-heading">
        <div>
          <span className="eyebrow">TAKE IT TO YOUR REPOSITORY</span>
          <h3>GitHub export</h3>
        </div>
        <span className="badge">Preview first</span>
      </div>
      <p>
        Prepare the generated files for the existing GitHub exporter. Publishing creates a fresh
        branch and an isolated project folder, with an optional draft pull request.
      </p>
      <form onSubmit={preview}>
        <label>
          Repository
          <input
            value={repo}
            onChange={(e) => {
              setRepo(e.target.value);
              setPlan(null);
            }}
            placeholder="your-name/your-repository"
            required
            maxLength={200}
          />
        </label>
        <label>
          Base branch
          <input
            value={base}
            onChange={(e) => {
              setBase(e.target.value);
              setPlan(null);
            }}
            required
            maxLength={200}
          />
        </label>
        <button type="submit">Preview GitHub export</button>
      </form>
      {message && <p role="alert">{message}</p>}
      {plan && (
        <div className="export-preview">
          <p>
            <strong>{plan.repository}</strong> · base <code>{plan.base}</code> · new{' '}
            <code>mini-devin/export-&lt;uuid&gt;</code> branch
          </p>
          <ul>
            {plan.files.map((file) => (
              <li key={file.path}>
                <code>{file.path}</code>
                <span>{file.bytes} bytes</span>
              </li>
            ))}
          </ul>
          <p>No GitHub changes have been made. Review the files, then download the handoff JSON.</p>
          <button
            type="button"
            onClick={() => {
              downloadJson({ files }, 'mini-devin-result.json');
              setMessage('Export JSON downloaded. No repository changes were made.');
            }}
          >
            Download export JSON
          </button>
          <details>
            <summary>Run the exporter locally</summary>
            <p>
              Place the downloaded JSON in your Mini-Devin checkout. The command below is an offline
              preview. Configure a repository-scoped <code>GITHUB_EXPORT_TOKEN</code> in your
              terminal environment only when publishing; never paste it into this page.
            </p>
            <pre>{plan.command}</pre>
            <p>
              After reviewing the preview, append <code>--apply --create-pr</code> to create a new
              branch and draft PR. The base branch is never overwritten.
            </p>
            <a
              href="https://github.com/aanyamehrotra/mini-devin/blob/main/docs/GITHUB_EXPORT.md"
              target="_blank"
              rel="noreferrer"
            >
              Full export guide ↗
            </a>
          </details>
        </div>
      )}
      <p className="muted">
        This web panel prepares an offline handoff. GitHub publishing runs through the CLI with your
        repository-scoped credential; the hosted app does not request or store GitHub tokens.
      </p>
    </section>
  );
}
