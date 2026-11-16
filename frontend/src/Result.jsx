import { useMemo, useState } from 'react';
import Prism from 'prismjs';
import 'prismjs/components/prism-python';
import { diffLines } from 'diff';
import { downloadProject, projectZip } from './project.js';
import { executeProject } from './stream.js';
import GitHubPanel from './GitHubPanel.jsx';

function tokens(nodes) {
  return nodes.map((node, i) =>
    typeof node === 'string' ? (
      node
    ) : (
      <span key={i} className={`token ${node.type}`}>
        {Array.isArray(node.content) ? tokens(node.content) : node.content}
      </span>
    )
  );
}
function Code({ text, path }) {
  const preview = text.slice(0, 30000);
  const highlighted = useMemo(
    () =>
      path.endsWith('.py') ? tokens(Prism.tokenize(preview, Prism.languages.python)) : preview,
    [preview, path]
  );
  return (
    <>
      <pre className="code" aria-label="File contents">
        <code>{highlighted || 'No generated files.'}</code>
      </pre>
      {text.length > preview.length && (
        <p className="muted">Preview shortened. Download the project for the complete file.</p>
      )}
    </>
  );
}
function Changes({ before, after }) {
  const parts = useMemo(
    () =>
      before.length + after.length < 60000
        ? diffLines(before, after, { timeout: 50, maxEditLength: 1000 })
        : undefined,
    [before, after]
  );
  return (
    <div className="diff-panel">
      <p className="muted">Previous attempt → selected attempt · additions and removals</p>
      {parts ? (
        <pre aria-label="Code changes">
          {parts.map((part, i) => (
            <span
              key={i}
              className={part.added ? 'diff-add' : part.removed ? 'diff-remove' : 'diff-same'}
            >
              {part.value
                .split('\n')
                .filter((line, j, lines) => j < lines.length - 1 || line)
                .map((line, j) => (
                  <span className="diff-line" key={j}>
                    {part.added ? '+ ' : part.removed ? '− ' : '  '}
                    {line}
                    {'\n'}
                  </span>
                ))}
            </span>
          ))}
        </pre>
      ) : (
        <p>
          These files are too large for a quick diff. Inspect each attempt or download the files.
        </p>
      )}
    </div>
  );
}

export default function Result({ result, accessToken = '', canExecute = false, onResult }) {
  const [attemptIndex, setAttemptIndex] = useState(result.attempts.length - 1);
  const [filePath, setFilePath] = useState('');
  const [tab, setTab] = useState('code');
  const [toast, setToast] = useState('');
  const [editing, setEditing] = useState(false);
  const [edits, setEdits] = useState({});
  const [github, setGithub] = useState(false);
  const [running, setRunning] = useState(false);
  const [extraFiles, setExtraFiles] = useState({});
  const [removedFiles, setRemovedFiles] = useState({});
  const [newPath, setNewPath] = useState('');
  const attempt = result.attempts[attemptIndex];
  const execution = attempt?.execution || result.execution;
  const originalFiles = (attempt?.code || result.code)?.files || [];
  const files = [...originalFiles, ...(extraFiles[attemptIndex] || [])]
    .filter((file) => !(removedFiles[attemptIndex] || []).includes(file.path))
    .map((file) => ({ ...file, content: edits[`${attemptIndex}:${file.path}`] ?? file.content }));
  const dirty =
    files.length !== originalFiles.length ||
    files.some(
      (file) =>
        file.content !== originalFiles.find((original) => original.path === file.path)?.content
    );
  function addFile(event) {
    event.preventDefault();
    const path = newPath.trim();
    try {
      if (
        [...originalFiles, ...(extraFiles[attemptIndex] || [])].some((file) => file.path === path)
      )
        throw new Error(
          'That path already exists in this attempt. Reset project edits to restore removed files.'
        );
      projectZip([...files, { path, content: '' }]);
      setExtraFiles((previous) => ({
        ...previous,
        [attemptIndex]: [...(previous[attemptIndex] || []), { path, content: '' }],
      }));
      setFilePath(path);
      setNewPath('');
      setEditing(true);
      setTab('code');
      setToast('File added to your browser copy.');
    } catch (error) {
      setToast(error.message);
    }
  }
  const file = files.find((f) => f.path === filePath) || files[0] || { path: '', content: '' };
  const previousFiles = result.attempts[attemptIndex - 1]?.code?.files || [];
  const changedPaths = [...new Set([...previousFiles, ...files].map((f) => f.path))].filter(
    (path) =>
      previousFiles.find((f) => f.path === path)?.content !==
      files.find((f) => f.path === path)?.content
  );
  const diffPath = changedPaths.includes(filePath)
    ? filePath
    : changedPaths.includes(file.path)
      ? file.path
      : changedPaths[0] || file.path;
  async function copy() {
    try {
      await navigator.clipboard.writeText(file.content);
      setToast('File copied.');
    } catch {
      setToast('Clipboard unavailable. Select the code to copy it.');
    }
  }
  async function runEdits() {
    setRunning(true);
    setToast('Running the edited project in Docker…');
    try {
      const next = await executeProject(files, accessToken);
      const number = result.attempts.length + 1;
      const updated = {
        ...result,
        ...next,
        manual_run: true,
        ui_key: result.ui_key || result.run_id || result.plan?.goal,
        run_id: undefined,
        attempts: [...result.attempts, { ...next, attempt: number }],
        timings: [
          ...(result.timings || []),
          { stage: 'manual execute', attempt: number, duration_ms: next.duration_ms },
        ],
      };
      setAttemptIndex(number - 1);
      setEdits({});
      setExtraFiles({});
      setRemovedFiles({});
      setEditing(false);
      onResult?.(updated);
      setToast(
        'Edited files executed. This manual run did not call the model or replace saved history.'
      );
    } catch (error) {
      setToast(error.message);
    } finally {
      setRunning(false);
    }
  }
  return (
    <section className="result" aria-label="Task results">
      {result.history_saved === false && (
        <p role="alert">
          This result could not be saved. Keep this page open or copy the generated files.
        </p>
      )}
      {result.public_demo && (
        <p className="demo-result-note">
          This demo result stays on this page. It is not added to the private workspace history.
        </p>
      )}
      <div className="section-heading">
        <div>
          <span className="eyebrow">
            {result.recorded ? 'RECORDED WALKTHROUGH' : 'YOUR PROJECT'}
          </span>
          <h2>{result.title || result.plan?.goal || 'Generated project'}</h2>
        </div>
        <span className={`badge ${result.attempts.at(-1)?.success ? 'success' : 'failed'}`}>
          {result.attempts.at(-1)?.success ? 'Completed' : 'Needs attention'}
        </span>
      </div>
      {result.provenance && <p className="provenance">{result.provenance}</p>}
      <div className="project-actions">
        <button
          type="button"
          onClick={() => {
            setEditing((value) => !value);
            setTab('code');
          }}
        >
          {editing ? 'View code' : 'Edit files'}
        </button>
        <button type="button" onClick={() => setGithub((value) => !value)}>
          Export to GitHub ↗
        </button>
        <span>
          {files.length} files · {result.attempts.length} attempts ·{' '}
          {result.recorded ? 'recorded' : 'live result'}
        </span>
      </div>
      <div className="file-operations">
        <button
          type="button"
          disabled={running || files.length < 2}
          onClick={() => {
            setRemovedFiles((previous) => ({
              ...previous,
              [attemptIndex]: [...(previous[attemptIndex] || []), file.path],
            }));
            setToast('File removed from the browser copy. Reset project edits to restore it.');
          }}
        >
          Remove selected file
        </button>
        <button
          type="button"
          disabled={running || !dirty}
          onClick={() => {
            setEdits({});
            setExtraFiles({});
            setRemovedFiles({});
            setToast('Original generated files restored.');
          }}
        >
          Reset project edits
        </button>
      </div>
      <div className="attempts">
        <label htmlFor="attempt">Attempt</label>
        <select
          id="attempt"
          value={attemptIndex}
          onChange={(e) => {
            setAttemptIndex(Number(e.target.value));
            setToast('');
            setEditing(false);
          }}
        >
          {result.attempts.map((a, i) => (
            <option value={i} key={a.attempt}>
              Attempt {a.attempt} · {a.success ? 'Passed' : 'Failed'}
            </option>
          ))}
        </select>
        <span>
          {execution?.execution_time ?? '—'}s · exit {execution?.exit_code ?? '—'}
        </span>
      </div>
      <div className="workbench">
        <div className="explorer">
          <div className="pane-title">
            PROJECT FILES <span>{files.length}</span>
          </div>
          <form className="new-file" onSubmit={addFile}>
            <input
              aria-label="New file path"
              placeholder="helpers.py"
              value={newPath}
              maxLength={200}
              disabled={running}
              onChange={(e) => setNewPath(e.target.value)}
            />
            <button type="submit" disabled={running || !newPath.trim()}>
              + Add file
            </button>
          </form>
          <div className="files" role="group" aria-label="Generated files">
            {files.map((f) => (
              <button
                type="button"
                key={f.path}
                className={f.path === file.path ? 'selected' : ''}
                aria-pressed={f.path === file.path}
                onClick={() => {
                  setFilePath(f.path);
                  setToast('');
                }}
              >
                <span aria-hidden="true">{f.path.endsWith('.py') ? 'py' : '↳'}</span>
                {f.path}
              </button>
            ))}
          </div>
        </div>
        <div className="editor">
          <div className="editor-toolbar">
            <div className="editor-tabs" role="group" aria-label="Project views">
              {[
                ['code', 'Code'],
                ['changes', 'Changes'],
                ['plan', 'Plan'],
              ].map(([id, label]) => (
                <button
                  type="button"
                  key={id}
                  aria-pressed={tab === id}
                  disabled={id === 'changes' && attemptIndex === 0}
                  onClick={() => setTab(id)}
                >
                  {label}
                  {id === 'changes' && attemptIndex > 0 ? ` (${changedPaths.length})` : ''}
                </button>
              ))}
            </div>
            <div className="editor-actions">
              <button type="button" onClick={copy}>
                Copy file
              </button>
              <button
                type="button"
                onClick={() => {
                  try {
                    downloadProject(files);
                    setToast('Project downloaded.');
                  } catch (error) {
                    setToast(error.message);
                  }
                }}
              >
                Download ZIP ↓
              </button>
            </div>
          </div>
          {tab === 'code' && (
            <>
              <div className="file-title">
                {file.path || 'No file selected'}
                <span>{editing ? 'browser editor' : dirty ? 'edited copy' : 'read only'}</span>
              </div>
              {editing ? (
                <textarea
                  className="source-editor"
                  aria-label="Edit file contents"
                  value={file.content}
                  maxLength={262144}
                  disabled={running}
                  spellCheck={false}
                  onChange={(e) =>
                    setEdits((previous) => ({
                      ...previous,
                      [`${attemptIndex}:${file.path}`]: e.target.value,
                    }))
                  }
                />
              ) : (
                <Code text={file.content} path={file.path} />
              )}
              {dirty && (
                <div className="edit-notice">
                  <p>
                    Unsaved browser edits. The console below still shows the last executed version.
                  </p>
                  {canExecute ? (
                    <button type="button" disabled={running} onClick={runEdits}>
                      {running ? 'Running…' : 'Run edited project'}
                    </button>
                  ) : (
                    <a href="/workspace">Ask for a workspace token to run edited files ↗</a>
                  )}
                  <button
                    type="button"
                    disabled={running}
                    onClick={() =>
                      setEdits((previous) => {
                        const next = { ...previous };
                        delete next[`${attemptIndex}:${file.path}`];
                        return next;
                      })
                    }
                  >
                    Reset this file
                  </button>
                </div>
              )}
            </>
          )}
          {tab === 'changes' &&
            (attemptIndex === 0 ? (
              <p>Select a later attempt to compare changes.</p>
            ) : (
              <>
                <label className="diff-picker">
                  Compare file{' '}
                  <select
                    aria-label="Compare file"
                    value={diffPath}
                    onChange={(e) => setFilePath(e.target.value)}
                  >
                    {changedPaths.map((path) => (
                      <option key={path}>{path}</option>
                    ))}
                  </select>
                </label>
                <Changes
                  before={previousFiles.find((f) => f.path === diffPath)?.content || ''}
                  after={files.find((f) => f.path === diffPath)?.content || ''}
                />
              </>
            ))}
          {tab === 'plan' && (
            <div className="plan-panel">
              <h3>Implementation plan</h3>
              <ol>
                {(result.plan?.steps || []).map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ol>
              <h3>Features</h3>
              <ul>
                {(result.plan?.features || []).map((feature, i) => (
                  <li key={i}>{feature}</li>
                ))}
              </ul>
              <p className="muted">{(result.plan?.technologies || []).join(' · ')}</p>
            </div>
          )}
        </div>
      </div>
      {toast && (
        <p className="action-status" role="status">
          {toast}
        </p>
      )}
      {github && <GitHubPanel files={files} />}
      <div className="terminal">
        <div className="pane-title">
          <span>
            <i className="terminal-dot" /> EXECUTION CONSOLE
          </span>
          <span>{execution?.success ? 'exit 0' : `exit ${execution?.exit_code ?? '—'}`}</span>
        </div>
        <div className="output">
          <h3>Output</h3>
          <pre>{execution?.stdout || 'No standard output.'}</pre>
        </div>
        {execution?.stderr && (
          <div className="output error-output">
            <h3>{execution.success ? 'Diagnostics' : 'Errors'}</h3>
            <pre>{execution.stderr}</pre>
          </div>
        )}
      </div>
      <p className="feedback">
        <strong>Review</strong>
        {(attempt?.review || result.review)?.feedback}
      </p>
      {(result.timings || []).length > 0 && (
        <details className="timing-details">
          <summary>Inspect stage timings · {result.timings.length} completed stages</summary>
          <ol>
            {result.timings.map((item, i) => (
              <li key={i}>
                <span>
                  {item.stage} · attempt {item.attempt}
                </span>
                <strong>{(item.duration_ms / 1000).toFixed(2)}s</strong>
              </li>
            ))}
          </ol>
        </details>
      )}
      {result.context && (
        <div className="references">
          <h3>References supplied</h3>
          {result.context.status === 'ready' ? (
            result.context.sources.map((source) => (
              <details key={source.citation}>
                <summary>{source.citation}</summary>
                <pre>{source.text}</pre>
              </details>
            ))
          ) : (
            <p>References were unavailable. This run continued without extra context.</p>
          )}
          <p>
            These references were supplied to the model; they do not prove the result is correct.
          </p>
        </div>
      )}
    </section>
  );
}
