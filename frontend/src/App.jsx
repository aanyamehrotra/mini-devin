import { useEffect, useRef, useState } from 'react';
import { runTask } from './stream.js';

const steps = [['plan', 'Plan', 'Understand the request'], ['generate', 'Build', 'Write and refine code'],
  ['execute', 'Run', 'Execute the project'], ['review', 'Review', 'Check the result']];
const errorMessages = {
  provider_failure: 'The model provider could not complete this step. Check its configuration and try again.',
  empty_response: 'The model returned an empty response. Please try again.',
  invalid_json: 'The model returned an unreadable response. Please try again.',
  invalid_schema: 'The model returned an incomplete response. Please try again.',
};
const examples = ['Print the first 10 Fibonacci numbers', 'Create a Python CSV summary tool'];

function Result({ result }) {
  const [attemptIndex, setAttemptIndex] = useState(result.attempts.length - 1);
  const [fileIndex, setFileIndex] = useState(0);
  const attempt = result.attempts[attemptIndex];
  const execution = attempt?.execution || result.execution;
  const files = (attempt?.code || result.code)?.files || [];
  const file = files[fileIndex] || files[0];
  return <section className="result" aria-label="Task results">
    <div className="section-heading"><div><span className="eyebrow">YOUR PROJECT</span><h2>{result.plan?.goal || 'Generated project'}</h2></div>
      <span className={`badge ${result.attempts.at(-1)?.success ? 'success' : 'failed'}`}>
        {result.attempts.at(-1)?.success ? 'Completed' : 'Needs attention'}</span></div>
    <div className="attempts"><label htmlFor="attempt">Attempt</label><select id="attempt" value={attemptIndex} onChange={e => {setAttemptIndex(Number(e.target.value)); setFileIndex(0);}}>
      {result.attempts.map((a, i) => <option value={i} key={a.attempt}>Attempt {a.attempt} · {a.success ? 'Passed' : 'Failed'}</option>)}</select>
      <span>{execution?.execution_time ?? '—'}s · exit {execution?.exit_code ?? '—'}</span></div>
    <div className="output-grid"><div className="output"><h3>Output</h3><pre>{execution?.stdout || 'No standard output.'}</pre></div>
      {execution?.stderr && <div className="output error-output"><h3>Errors</h3><pre>{execution.stderr}</pre></div>}</div>
    <p className="feedback"><strong>Review</strong> {(attempt?.review || result.review)?.feedback}</p>
    {result.context && <div className="references"><h3>References supplied</h3>
      {result.context.status === 'ready' ? result.context.sources.map(source => <details key={source.citation}><summary>{source.citation}{source.truncated ? ' · excerpt shortened' : ''}</summary><pre>{source.text}</pre></details>) :
        <p>{result.context.status === 'no_matches' ? 'No matching references were found.' : 'References were unavailable. This run continued without extra context.'}</p>}
      <p>These references were supplied to the model; they do not prove the result is correct.</p></div>}
    <div className="file-panel"><div className="files" role="group" aria-label="Generated files">{files.map((f, i) =>
      <button type="button" key={`${i}-${f.path}`} className={i === fileIndex ? 'selected' : ''} aria-pressed={i === fileIndex} onClick={() => setFileIndex(i)}>{f.path}</button>)}</div>
      <pre className="code" aria-label="File contents"><code>{file?.content || 'No generated files.'}</code></pre></div>
  </section>;
}

export default function App() {
  const [prompt, setPrompt] = useState('');
  const [useContext, setUseContext] = useState(false);
  const [accessToken, setAccessToken] = useState('');
  const [status, setStatus] = useState('idle');
  const [events, setEvents] = useState([]);
  const [message, setMessage] = useState('');
  const [result, setResult] = useState(null);
  const controller = useRef(null);
  const busy = status === 'running';
  useEffect(() => () => controller.current?.abort(), []);

  async function submit(event) {
    event.preventDefault();
    if (busy || !prompt.trim()) return;
    const request = new AbortController();
    controller.current = request;
    setStatus('running'); setEvents([]); setMessage(''); setResult(null);
    try {
      await runTask(prompt.trim(), item => {
        if (request.signal.aborted) return;
        if (item.type === 'stage') setEvents(previous => [...previous, item.data]);
        if (item.type === 'complete') {setResult(item.data.result); setStatus(item.data.success ? 'complete' : 'failed');}
        if (item.type === 'error') {setStatus('error'); setMessage(errorMessages[item.data.error] || 'The task could not be completed. Please try again.');}
        if (item.type === 'cancelled') {setStatus('stopped'); setMessage('Updates stopped. Work already running may finish.');}
      }, request.signal, useContext, accessToken);
    } catch (error) {
      if (error.name === 'AbortError') {setStatus('stopped'); setMessage('Updates stopped. Work already running may finish.');}
      else {setStatus('error'); setMessage(error.message || 'The request could not be completed.');}
    } finally { if (controller.current === request) controller.current = null; }
  }

  const last = events.at(-1);
  return <div className="shell"><aside>
    <a className="brand" href="/" aria-label="Mini-Devin home"><span className="brand-icon">m<span>·</span></span>mini-devin</a>
    <div className="workspace-label">WORKSPACE</div><div className="nav-active"><span>⌘</span> Build a project</div>
    <div className="sidebar-note"><span className="small-dot"/> Your coding workspace<p>From a clear idea<br/>to a reviewed project.</p></div>
    <footer>Plan. Build. Run. Review.</footer>
  </aside><main>
    <header><span>Workspace <span className="slash">/</span> New task</span><span className="local-label">PYTHON PROJECTS</span></header>
    <div className="content"><div className="intro"><span className="eyebrow">LET’S MAKE SOMETHING</span><h1>What would you like to build?</h1>
      <p>Describe a Python project. Follow the plan, inspect the code,<br className="desktop-break"/> and see how it runs—all in one place.</p></div>
      <form onSubmit={submit} className="composer"><label htmlFor="task">Your task</label>
        <textarea id="task" placeholder="Build a Python tool that…" rows={4} value={prompt} disabled={busy} onChange={e => setPrompt(e.target.value)} required/>
        <div className="composer-bottom"><span>Be specific about the result you want.</span>
          {busy ? <button type="button" className="stop" onClick={() => controller.current?.abort()}>Stop updates</button> :
            <button className="primary" type="submit" disabled={!prompt.trim()}>Build project <span>↗</span></button>}</div>
      </form>
      <details className="access-settings"><summary>Workspace access</summary><label htmlFor="access-token">Workspace access token (if configured)</label><input id="access-token" type="password" value={accessToken} disabled={busy} autoComplete="off" onChange={e => setAccessToken(e.target.value)}/><p>This is a workspace password, not your model API key. It stays in memory until you close or reload this page.</p></details>
      <label className="context-toggle"><input type="checkbox" checked={useContext} disabled={busy} onChange={e => setUseContext(e.target.checked)}/><span>Use project references<small>Excerpts from the configured code/docs are sent to your model provider.</small></span></label>
      {status === 'idle' && <div className="examples"><span>Try a starting point</span>{examples.map(example => <button type="button" key={example} onClick={() => setPrompt(example)}>{example} <span>↗</span></button>)}</div>}
      <section className="progress" aria-label="Agent progress"><div className="section-heading"><h2>The workflow</h2>
        <span className="workflow-state" role="status">{busy ? `Working${last ? ` · attempt ${last.attempt || 1}` : ''}` :
          ({idle:'Ready when you are', complete:'Finished', failed:'Finished with issues', error:'Request failed', stopped:'Updates stopped'})[status]}</span></div>
        <ol className="steps">{steps.map(([key, title, description], index) => {
          const done = events.some(e => e.stage === key && (key === 'plan' || !last?.attempt || (e.attempt || 1) === (last.attempt || 1)));
          return <li key={key} className={done ? 'done' : ''}><span className="step-number">{done ? '✓' : `0${index+1}`}</span><div><h3>{title}</h3><p>{description}</p></div></li>;
        })}</ol>
      </section>
      {message && <div className={`notice ${status === 'error' ? 'notice-error' : ''}`} role="alert">{message}</div>}
      {result && <Result result={result}/>}
      {!result && !busy && !message && <div className="empty"><span className="empty-icon">⌁</span><h3>A little context goes a long way.</h3><p>Include sample inputs, expected output, and any packages you want to use.<br/>Your generated files and execution results will appear here.</p></div>}
      <div className="page-foot">Generated code should be reviewed before use. <span>Progress is saved for this session only.</span></div>
    </div>
  </main></div>;
}
