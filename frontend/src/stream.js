// SSE parsing is independent of network chunk boundaries and UTF-8 byte splits.
export async function readEvents(body, onEvent, signal) {
  if (!body) throw new Error('The server did not provide a response stream.');
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let terminal = false;
  function dispatch(block) {
    const lines = block.split(/\r?\n/);
    let type = 'message';
    const data = [];
    for (const line of lines) {
      if (line.startsWith('event:')) type = line.slice(6).trim();
      if (line.startsWith('data:')) data.push(line.slice(5).replace(/^ /, ''));
    }
    if (!data.length) return;
    let payload;
    try { payload = JSON.parse(data.join('\n')); }
    catch { throw new Error('The server sent an invalid progress update.'); }
    if (type === 'complete' && (!payload?.result || !Array.isArray(payload.result.attempts) || !payload.result.attempts.length)) {
      throw new Error('The server returned an incomplete project result.');
    }
    onEvent({ type, data: payload });
    terminal = ['complete', 'error', 'cancelled'].includes(type);
  }
  try {
    while (!terminal) {
      if (signal?.aborted) throw new DOMException('Stopped', 'AbortError');
      const { done, value } = await reader.read();
      buffer += done ? decoder.decode() : decoder.decode(value, { stream: true });
      let separator;
      while (!terminal && (separator = /\r?\n\r?\n/.exec(buffer))) {
        dispatch(buffer.slice(0, separator.index));
        buffer = buffer.slice(separator.index + separator[0].length);
      }
      if (done) break;
    }
    if (!terminal) throw new Error('The connection ended before a final result. Please try again.');
  } finally {
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}

export async function runTask(prompt, onEvent, signal) {
  const response = await fetch('/api/chat/stream', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt }), signal,
  });
  if (!response.ok) throw new Error(`The request failed (${response.status}). Check the backend and try again.`);
  if (!response.headers.get('content-type')?.includes('text/event-stream')) {
    throw new Error('The backend returned an unexpected response.');
  }
  return readEvents(response.body, onEvent, signal);
}
