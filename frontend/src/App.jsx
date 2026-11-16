import { useEffect, useRef, useState } from 'react';
import { runTask, savedRuns } from './stream.js';
import Result from './Result.jsx';
import Showcases, { Engineering } from './Showcases.jsx';

const steps = [
  ['plan', 'Plan', 'Understand the request'],
  ['generate', 'Build', 'Write and refine code'],
  ['execute', 'Run', 'Execute the project'],
  ['review', 'Review', 'Check the result'],
];
const errorMessages = {
  provider_failure:
    'The model provider could not complete this step. Check its configuration and try again.',
  empty_response: 'The model returned an empty response. Please try again.',
  invalid_json: 'The model returned an unreadable response. Please try again.',
  invalid_schema: 'The model returned an incomplete response. Please try again.',
  demo_provider_unavailable:
    'Live generation is temporarily unavailable. Explore a completed project above without using any quota.',
  demo_unavailable:
    'This live run could not finish. The recorded walkthroughs above are still available.',
};
const examples = ['Print the first 10 Fibonacci numbers', 'Create a Python CSV summary tool'];
const demoExamples = [
  ['csv-quality', 'Audit missing cells and duplicate CSV records'],
  ['log-analyzer', 'Generate a multi-file log analyser'],
  ['average-fix', 'Fix an average calculation'],
  ['fibonacci', 'Print the first 10 Fibonacci numbers'],
  ['csv', 'Summarize sample CSV scores'],
];

export default function App() {
  const demo =
    import.meta.env.VITE_PUBLIC_DEMO === 'true' && window.location.pathname !== '/workspace';
  const [demoTask, setDemoTask] = useState('csv-quality');
  const [prompt, setPrompt] = useState('');
  const [history, setHistory] = useState([]);
  const [useContext, setUseContext] = useState(false);
  const [accessToken, setAccessToken] = useState('');
  const [status, setStatus] = useState('idle');
  const [events, setEvents] = useState([]);
  const [message, setMessage] = useState('');
  const [result, setResult] = useState(null);
  const controller = useRef(null);
  const resultAnchor = useRef(null);
  const [elapsed, setElapsed] = useState(0);
  const busy = status === 'running';
  useEffect(() => () => controller.current?.abort(), []);
  useEffect(() => {
    if (!busy) return;
    const started = Date.now();
    setElapsed(0);
    const timer = setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 1000);
    return () => clearInterval(timer);
  }, [busy]);
  function explore(recording) {
    setResult(recording);
    setStatus(recording.attempts.at(-1)?.success ? 'complete' : 'failed');
    setMessage('');
    setEvents((recording.timings || []).map((item) => ({ ...item, status: 'completed' })));
    setTimeout(
      () => resultAnchor.current?.scrollIntoView?.({ behavior: 'smooth', block: 'start' }),
      50
    );
  }

  async function submit(event) {
    event.preventDefault();
    if (busy || (!demo && !prompt.trim())) return;
    const request = new AbortController();
    controller.current = request;
    setStatus('running');
    setEvents([]);
    setMessage(
      demo
        ? 'Demo access is limited: three runs per visitor per day, twenty runs total per day, and one active project at a time. Please wait a minute between runs. For full access, ask the project owner for a workspace access token.'
        : ''
    );
    setResult(null);
    try {
      await runTask(
        prompt.trim(),
        (item) => {
          if (request.signal.aborted) return;
          if (item.type === 'stage') setEvents((previous) => [...previous, item.data]);
          if (item.type === 'complete') {
            setResult(item.data.result);
            setStatus(item.data.success ? 'complete' : 'failed');
          }
          if (item.type === 'error') {
            setStatus('error');
            setMessage(
              errorMessages[item.data.error] || 'The task could not be completed. Please try again.'
            );
          }
          if (item.type === 'cancelled') {
            setStatus('stopped');
            setMessage('Updates stopped. Work already running may finish.');
          }
        },
        request.signal,
        useContext,
        accessToken,
        demo ? demoTask : ''
      );
    } catch (error) {
      if (error.name === 'AbortError') {
        setStatus('stopped');
        setMessage('Updates stopped. Work already running may finish.');
      } else {
        setStatus('error');
        setMessage(
          (error.message || 'The request could not be completed.') +
            (demo
              ? ' Explore a completed project above while you wait. For full access, ask the project owner for a workspace access token.'
              : '')
        );
      }
    } finally {
      if (controller.current === request) controller.current = null;
    }
  }

  async function loadHistory(identifier = '') {
    try {
      const data = await savedRuns(accessToken, identifier);
      if (identifier) {
        setResult(data.result);
        setPrompt(data.prompt);
        setMessage('');
        setStatus(data.result.attempts.at(-1)?.success ? 'complete' : 'failed');
        setEvents(steps.map(([stage]) => ({ stage, attempt: data.result.attempts.length })));
      } else setHistory(data.runs);
    } catch (error) {
      setMessage(error.message);
    }
  }
  const last = events.at(-1);
  return (
    <>
      <a className="skip-link" href="#main-content">
        Skip to workspace
      </a>
      <div className="shell">
        <aside>
          <a className="brand" href="/" aria-label="Mini-Devin home">
            <span className="brand-icon">
              m<span>·</span>
            </span>
            mini-devin
          </a>
          <div className="workspace-label">{demo ? 'PUBLIC DEMO' : 'WORKSPACE'}</div>
          <div className="nav-active">
            <span>⌘</span> {demo ? 'Try Mini-Devin' : 'Build a project'}
          </div>
          <nav className="sidebar-links" aria-label="Project links">
            <a href="#engineering">Engineering notes ↗</a>
            <a href="https://github.com/aanyamehrotra/mini-devin" target="_blank" rel="noreferrer">
              Source on GitHub ↗
            </a>
          </nav>
          <div className="sidebar-note">
            <span className="small-dot" /> Your coding workspace
            <p>
              From a clear idea
              <br />
              to a reviewed project.
            </p>
          </div>
          <footer>Plan. Build. Run. Review.</footer>
        </aside>
        <main id="main-content">
          <header>
            <span>
              Workspace <span className="slash">/</span> New task
            </span>
            <span className="local-label">PYTHON PROJECTS</span>
          </header>
          <div className="content">
            <div className="intro">
              <span className="eyebrow">LET’S MAKE SOMETHING</span>
              <h1>
                {demo ? (
                  <>
                    From an idea.
                    <br />
                    <span className="hero-accent">To code that runs.</span>
                  </>
                ) : (
                  'What would you like to build?'
                )}
              </h1>
              <p>
                {demo ? (
                  'An observable AI coding workspace. Follow the plan, inspect the files, and see what actually happened when the code ran.'
                ) : (
                  <>
                    Describe a Python project. Follow the plan, inspect the code,
                    <br className="desktop-break" /> and see how it runs—all in one place.
                  </>
                )}
              </p>
            </div>
            {demo && <Showcases onSelect={explore} busy={busy} />}
            {result?.recorded && (
              <div ref={resultAnchor}>
                <Result key={result.plan?.goal} result={result} />
              </div>
            )}
            {demo && (
              <div className="live-heading">
                <span className="eyebrow">WANT TO TRY IT YOURSELF?</span>
                <h2>Run a fresh project</h2>
                <p>A new generation using the real model and Docker. No sign-in needed.</p>
              </div>
            )}
            {demo && (
              <details className="demo-info">
                <summary>Live demo access & limits</summary>
                <p>
                  Three runs per visitor each day, with twenty runs shared across the demo. One
                  project runs at a time, with a one-minute shared cooldown for free model limits.
                  Results are private to this page.
                </p>
                <p>
                  For full access, ask the project owner for a workspace access token. Already have
                  one? <a href="/workspace">Open the private workspace</a>.
                </p>
              </details>
            )}
            <form onSubmit={submit} className="composer">
              <label htmlFor="task">{demo ? 'Choose an example' : 'Your task'}</label>
              {demo ? (
                <select
                  id="task"
                  className="demo-select"
                  value={demoTask}
                  disabled={busy}
                  onChange={(e) => {
                    setDemoTask(e.target.value);
                    setMessage(
                      'Demo access is limited to these examples: three runs per visitor each day, twenty runs shared across all visitors, and one project at a time. For full access, ask the project owner for a workspace access token.'
                    );
                  }}
                >
                  {demoExamples.map(([id, label]) => (
                    <option key={id} value={id}>
                      {label}
                    </option>
                  ))}
                </select>
              ) : (
                <textarea
                  id="task"
                  placeholder="Build a Python tool that…"
                  rows={4}
                  value={prompt}
                  disabled={busy}
                  onChange={(e) => setPrompt(e.target.value)}
                  required
                />
              )}
              <div className="composer-bottom">
                <span>
                  {demo
                    ? 'Real AI generation and sandboxed execution.'
                    : 'Be specific about the result you want.'}
                </span>
                {busy ? (
                  <button
                    type="button"
                    className="stop"
                    onClick={() => controller.current?.abort()}
                  >
                    Stop updates
                  </button>
                ) : (
                  <button className="primary" type="submit" disabled={!demo && !prompt.trim()}>
                    {demo ? 'Run live demo' : 'Build project'} <span>↗</span>
                  </button>
                )}
              </div>
            </form>
            {!demo && (
              <>
                <details className="access-settings">
                  <summary>Workspace access</summary>
                  <label htmlFor="access-token">Workspace access token (if configured)</label>
                  <input
                    id="access-token"
                    type="password"
                    value={accessToken}
                    disabled={busy}
                    autoComplete="off"
                    onChange={(e) => setAccessToken(e.target.value)}
                  />
                  <p>
                    This is a workspace password, not your model API key. It stays in memory until
                    you close or reload this page.
                  </p>
                </details>
                <label className="context-toggle">
                  <input
                    type="checkbox"
                    checked={useContext}
                    disabled={busy}
                    onChange={(e) => setUseContext(e.target.checked)}
                  />
                  <span>
                    Use project references
                    <small>
                      Excerpts from the configured code/docs are sent to your model provider.
                    </small>
                  </span>
                </label>
                {status === 'idle' && (
                  <div className="examples">
                    <span>Try a starting point</span>
                    {examples.map((example) => (
                      <button type="button" key={example} onClick={() => setPrompt(example)}>
                        {example} <span>↗</span>
                      </button>
                    ))}
                  </div>
                )}
                <section className="saved-runs">
                  <button type="button" disabled={busy} onClick={() => loadHistory()}>
                    Load saved runs
                  </button>
                  <span>Latest 100 results retained locally.</span>
                  {history.length > 0 && (
                    <ul>
                      {history.map((run) => (
                        <li key={run.id}>
                          <button type="button" disabled={busy} onClick={() => loadHistory(run.id)}>
                            {run.success ? '✓' : '!'} {run.goal}
                            <small>{new Date(run.created_at).toLocaleString()}</small>
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </section>
              </>
            )}
            <section className="progress" aria-label="Agent progress">
              <div className="section-heading">
                <h2>The workflow</h2>
                <span className="workflow-state" role="status">
                  {busy
                    ? `Working · ${elapsed}s${last ? ` · attempt ${last.attempt || 1}` : ''}`
                    : {
                        idle: 'Ready when you are',
                        complete: 'Finished',
                        failed: 'Finished with issues',
                        error: 'Request failed',
                        stopped: 'Updates stopped',
                      }[status]}
                </span>
              </div>
              <ol className="steps">
                {steps.map(([key, title, description], index) => {
                  const measured = events.filter((e) => e.stage === key).at(-1);
                  const active =
                    busy &&
                    (last ? steps.findIndex(([stage]) => stage === last.stage) + 1 : 0) === index;
                  const done = events.some(
                    (e) =>
                      e.stage === key &&
                      (key === 'plan' || !last?.attempt || (e.attempt || 1) === (last.attempt || 1))
                  );
                  return (
                    <li key={key} className={done ? 'done' : active ? 'active' : ''}>
                      <span className="step-number">{done ? '✓' : `0${index + 1}`}</span>
                      <div>
                        <h3>{title}</h3>
                        <p>
                          {measured?.duration_ms != null
                            ? `${(measured.duration_ms / 1000).toFixed(2)}s · completed`
                            : active
                              ? 'In progress…'
                              : description}
                        </p>
                      </div>
                    </li>
                  );
                })}
              </ol>
            </section>
            {message && (
              <div className={`notice ${status === 'error' ? 'notice-error' : ''}`} role="alert">
                {message}
              </div>
            )}
            {result && !result.recorded && (
              <div ref={resultAnchor}>
                <Result key={result.run_id || result.plan?.goal} result={result} />
              </div>
            )}
            {!result && !busy && !message && (
              <div className="empty">
                <span className="empty-icon">⌁</span>
                <h3>{demo ? 'See the whole workflow.' : 'A little context goes a long way.'}</h3>
                <p>
                  {demo ? (
                    'Watch each stage, then inspect the generated Python code and its actual output.'
                  ) : (
                    <>
                      Include sample inputs, expected output, and any packages you want to use.
                      <br />
                      Your generated files and execution results will appear here.
                    </>
                  )}
                </p>
              </div>
            )}
            {demo && <Engineering />}
            <div className="page-foot">
              Generated code should be reviewed before use.{' '}
              <span>
                {demo ? (
                  <>
                    <a
                      href="https://github.com/aanyamehrotra/mini-devin"
                      target="_blank"
                      rel="noreferrer"
                    >
                      View on GitHub
                    </a>{' '}
                    · <a href="/workspace">Private workspace</a>
                  </>
                ) : (
                  'Completed runs are archived locally when storage is available.'
                )}
              </span>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
