import { useEffect, useState } from 'react';
import catalog from './showcase-index.json';

export default function Showcases({ onSelect, busy }) {
  const [loading, setLoading] = useState('');
  const [error, setError] = useState('');
  async function open(id) {
    setLoading(id);
    setError('');
    try {
      const response = await fetch(`/showcases/${id}.json`);
      if (!response.ok) throw new Error('This walkthrough could not be loaded. Please try again.');
      const recording = await response.json();
      if (!recording.result?.attempts?.length) throw new Error('This walkthrough is unavailable.');
      onSelect({
        ...recording.result,
        recorded: true,
        title: recording.title,
        provenance: recording.provenance,
        recorded_at: recording.recorded_at,
      });
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading('');
    }
  }
  return (
    <section className="showcase-section" aria-label="Recorded examples">
      <div className="section-heading">
        <div>
          <span className="eyebrow">START HERE · NO QUOTA NEEDED</span>
          <h2>Explore a completed project</h2>
        </div>
        <span className="section-note">Recorded results, real executions</span>
      </div>
      <div className="showcase-grid">
        {catalog.map((item) => (
          <button
            className={`showcase-card ${item.id === 'repair' ? 'repair-card' : ''}`}
            type="button"
            key={item.id}
            disabled={busy || !!loading}
            onClick={() => open(item.id)}
          >
            <span className="card-top">
              <span className="card-icon" aria-hidden="true">
                {item.icon}
              </span>
              <span className="card-tag">{item.tag}</span>
            </span>
            <h3>{item.title}</h3>
            <p>{item.description}</p>
            <span className="card-bottom">
              {loading === item.id ? 'Loading…' : item.detail}
              <span aria-hidden="true">↗</span>
            </span>
          </button>
        ))}
      </div>
      {error && (
        <p className="notice notice-error" role="alert">
          {error}
        </p>
      )}
      <details className="demo-video">
        <summary>Watch a short workspace walkthrough</summary>
        <video
          controls
          preload="none"
          poster="/showcases/preview.jpg"
          src="/showcases/demo.mp4"
          aria-label="Mini-Devin workspace walkthrough"
        >
          Your browser cannot play this video.{' '}
          <a href="/showcases/demo.mp4">Download the walkthrough</a>.
        </video>
      </details>
      <p className="showcase-caption">
        These saved walkthroughs work even when live quota is used up. They do not start a new AI
        request.
      </p>
    </section>
  );
}

export function Engineering() {
  const [report, setReport] = useState(null);
  useEffect(() => {
    const controller = new AbortController();
    fetch('/showcases/benchmark.json', { signal: controller.signal })
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => {
        if (!controller.signal.aborted) setReport(data);
      })
      .catch(() => {});
    return () => controller.abort();
  }, []);
  return (
    <section className="engineering" id="engineering">
      <div className="section-heading">
        <div>
          <span className="eyebrow">BEYOND THE CHAT WINDOW</span>
          <h2>Built to be inspected</h2>
        </div>
        <a
          href="https://github.com/aanyamehrotra/mini-devin/blob/main/docs/ARCHITECTURE.md"
          target="_blank"
          rel="noreferrer"
        >
          Architecture ↗
        </a>
      </div>
      <div className="engineering-grid">
        <article>
          <h3>Observable workflow</h3>
          <p>
            Stage timings, execution output, review feedback, and an inspectable history of repair
            attempts.
          </p>
        </article>
        <article>
          <h3>Bounded execution</h3>
          <p>
            Python runs in Docker with time, CPU, memory, output, and network restrictions. Private
            history stays behind workspace access.
          </p>
        </article>
        <article>
          <h3>Independent checks</h3>
          <p>
            Fixed tasks are checked against expected output and required files. Model review is
            reported separately.
          </p>
        </article>
      </div>
      {report?.summary && (
        <>
          <div className="benchmark-stats">
            <div>
              <strong>
                {report.summary.passed}/{report.summary.tasks}
              </strong>
              <span>fixed tasks passed</span>
            </div>
            <div>
              <strong>{report.summary.median_seconds}s</strong>
              <span>median completion</span>
            </div>
            <div>
              <strong>{report.summary.total_attempts}</strong>
              <span>total execution attempts</span>
            </div>
          </div>
          <p className="showcase-caption">
            Measured {new Date(report.recorded_at).toLocaleDateString()} · {report.model}. Five
            small fixed tasks, one run per task; not a general coding benchmark.{' '}
            <a href="https://github.com/aanyamehrotra/mini-devin/blob/main/docs/EVALUATION.md">
              Method and full results ↗
            </a>
          </p>
        </>
      )}
    </section>
  );
}
