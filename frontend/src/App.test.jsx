import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App.jsx';
import { runTask, savedRuns, executeProject } from './stream.js';
vi.mock('./stream.js', () => ({ runTask: vi.fn(), savedRuns: vi.fn(), executeProject: vi.fn() }));

const code = {
  files: [
    { path: 'main.py', content: 'print("hello")' },
    { path: 'helper.py', content: 'answer = 42' },
  ],
};
const execution = { stdout: 'hello output', stderr: '', exit_code: 0, execution_time: 0.1 };
const review = { feedback: 'Matches the request' };
const result = {
  plan: { goal: 'Print hello' },
  code,
  execution,
  review,
  attempts: [
    {
      attempt: 1,
      success: false,
      code,
      execution: { ...execution, stdout: 'first attempt', stderr: 'NameError' },
      review: { feedback: 'Fix the name' },
    },
    { attempt: 2, success: true, code, execution, review },
  ],
};
beforeEach(() => vi.resetAllMocks());

async function start() {
  const user = userEvent.setup();
  render(<App />);
  await user.type(screen.getByLabelText('Your task'), 'Print hello');
  await user.click(screen.getByRole('button', { name: /Build project/ }));
  return user;
}

describe('workspace', () => {
  it('disables an empty submission and fills example prompts', async () => {
    const user = userEvent.setup();
    render(<App />);
    expect(screen.getByRole('button', { name: /Build project/ }).disabled).toBe(true);
    await user.click(screen.getByRole('button', { name: /Fibonacci/ }));
    expect(screen.getByLabelText('Your task').value).toContain('Fibonacci');
  });
  it('renders results, switches files and inspects failed attempts', async () => {
    runTask.mockImplementation(async (prompt, onEvent) => {
      onEvent({ type: 'stage', data: { stage: 'plan', status: 'completed' } });
      onEvent({ type: 'complete', data: { success: true, result } });
    });
    const user = await start();
    expect(await screen.findByText('hello output')).toBeTruthy();
    expect(screen.getByLabelText('File contents').textContent).toContain('print("hello")');
    await user.click(screen.getByRole('button', { name: 'helper.py' }));
    expect(screen.getByLabelText('File contents').textContent).toContain('answer = 42');
    await user.selectOptions(screen.getByLabelText('Attempt'), '0');
    expect(screen.getByText('first attempt')).toBeTruthy();
    expect(screen.getByText('NameError')).toBeTruthy();
    expect(screen.getByText('Fix the name')).toBeTruthy();
  });
  it('displays a provider error and allows retry', async () => {
    runTask.mockImplementation(async (prompt, onEvent) =>
      onEvent({ type: 'error', data: { stage: 'planner', error: 'provider_failure' } })
    );
    await start();
    expect((await screen.findByRole('alert')).textContent).toContain('model provider');
    expect(screen.getByRole('button', { name: /Build project/ }).disabled).toBe(false);
  });
  it('stops updates using AbortController without claiming work was killed', async () => {
    runTask.mockImplementation(
      (prompt, onEvent, signal) =>
        new Promise((resolve, reject) => {
          signal.addEventListener('abort', () => reject(new DOMException('Stopped', 'AbortError')));
        })
    );
    const user = await start();
    await user.click(screen.getByRole('button', { name: 'Stop updates' }));
    expect((await screen.findByRole('alert')).textContent).toContain(
      'Work already running may finish'
    );
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /Build project/ }).disabled).toBe(false)
    );
  });
  it('shows transport errors without losing the prompt', async () => {
    runTask.mockRejectedValue(new Error('The connection ended before a final result.'));
    await start();
    expect((await screen.findByRole('alert')).textContent).toContain('connection ended');
    expect(screen.getByLabelText('Your task').value).toBe('Print hello');
  });
});

it('keeps references off by default and submits explicit opt-in', async () => {
  runTask.mockImplementation(async (prompt, onEvent) =>
    onEvent({ type: 'error', data: { error: 'provider_failure' } })
  );
  const user = userEvent.setup();
  render(<App />);
  const checkbox = screen.getByRole('checkbox', { name: /Use project references/ });
  expect(checkbox.checked).toBe(false);
  await user.click(checkbox);
  await user.type(screen.getByLabelText('Your task'), 'hello');
  await user.click(screen.getByRole('button', { name: /Build project/ }));
  expect(runTask.mock.calls[0][3]).toBe(true);
});

it('shows supplied citations and excerpts without claiming proven grounding', async () => {
  const context = {
    status: 'ready',
    sources: [{ citation: 'guide.md:1-2', text: 'A useful example', truncated: false }],
  };
  runTask.mockImplementation(async (prompt, onEvent) =>
    onEvent({ type: 'complete', data: { success: true, result: { ...result, context } } })
  );
  await start();
  expect(await screen.findByText('guide.md:1-2')).toBeTruthy();
  expect(screen.getByText('A useful example')).toBeTruthy();
  expect(screen.getByText(/do not prove the result is correct/)).toBeTruthy();
});

it('passes an optional workspace token from memory', async () => {
  runTask.mockImplementation(async (prompt, onEvent) =>
    onEvent({ type: 'error', data: { error: 'provider_failure' } })
  );
  const user = userEvent.setup();
  render(<App />);
  await user.click(screen.getByText('Workspace access'));
  await user.type(
    screen.getByLabelText('Workspace access token (if configured)'),
    'workspace-fixture'
  );
  await user.type(screen.getByLabelText('Your task'), 'hello');
  await user.click(screen.getByRole('button', { name: /Build project/ }));
  expect(runTask.mock.calls[0][4]).toBe('workspace-fixture');
  expect(screen.getByLabelText('Workspace access token (if configured)').type).toBe('password');
});

it('loads an archived run and renders its result', async () => {
  savedRuns
    .mockResolvedValueOnce({
      runs: [
        {
          id: 'saved-id',
          goal: 'Archived project',
          success: true,
          created_at: '2026-11-16T00:00:00Z',
        },
      ],
    })
    .mockResolvedValueOnce({
      prompt: 'archived prompt',
      result: { ...result, run_id: 'saved-id' },
    });
  const user = userEvent.setup();
  render(<App />);
  await user.click(screen.getByRole('button', { name: 'Load saved runs' }));
  await user.click(await screen.findByRole('button', { name: /Archived project/ }));
  expect(await screen.findByText('hello output')).toBeTruthy();
  expect(screen.getByLabelText('Your task').value).toBe('archived prompt');
});

it('public demo needs no token, shows limits on selection/run, and hides private history', async () => {
  vi.stubEnv('VITE_PUBLIC_DEMO', 'true');
  try {
    runTask.mockImplementation(async (prompt, onEvent) =>
      onEvent({
        type: 'complete',
        data: { success: true, result: { ...result, public_demo: true } },
      })
    );
    const user = userEvent.setup();
    render(<App />);
    expect(screen.queryByText('Workspace access')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Load saved runs' })).toBeNull();
    await user.selectOptions(screen.getByLabelText('Start from'), 'csv');
    expect(screen.getByRole('alert').textContent).toContain('Demo access is limited');
    await user.click(screen.getByRole('button', { name: /Run live demo/ }));
    expect(runTask.mock.calls[0][5]).toBe('csv');
    expect(runTask.mock.calls[0][4]).toBe('');
    expect(screen.getByRole('alert').textContent).toContain('twenty runs total per day');
    expect(screen.getByText(/not added to the private workspace history/)).toBeTruthy();
  } finally {
    vi.unstubAllEnvs();
  }
});

it('shows a repair diff and the implementation plan', async () => {
  const fixed = {
    ...result,
    attempts: [
      result.attempts[0],
      {
        ...result.attempts[1],
        code: { files: [{ path: 'main.py', content: 'print("repaired")' }] },
      },
    ],
  };
  runTask.mockImplementation(async (prompt, onEvent) =>
    onEvent({ type: 'complete', data: { success: true, result: fixed } })
  );
  const user = await start();
  await user.click(screen.getByRole('button', { name: /Changes/ }));
  expect(screen.getByLabelText('Code changes').textContent).toContain('repaired');
  expect(screen.getByLabelText('Code changes').textContent).toContain('hello');
  await user.click(screen.getByRole('button', { name: 'Plan', exact: true }));
  expect(screen.getByText('Implementation plan')).toBeTruthy();
});

it('recorded examples remain available without live quota and do not call the model endpoint', async () => {
  vi.stubEnv('VITE_PUBLIC_DEMO', 'true');
  const mock = vi
    .spyOn(globalThis, 'fetch')
    .mockImplementation(
      async (url) =>
        new Response(
          JSON.stringify(
            url.includes('benchmark') ? {} : { result, provenance: 'Recorded test execution' }
          ),
          { headers: { 'Content-Type': 'application/json' } }
        )
    );
  try {
    const user = userEvent.setup();
    render(<App />);
    await user.click(screen.getByRole('button', { name: /Watch a bug get fixed/ }));
    expect(await screen.findByText('Recorded test execution')).toBeTruthy();
    expect(screen.getByText('RECORDED WALKTHROUGH')).toBeTruthy();
    expect(runTask).not.toHaveBeenCalled();
  } finally {
    mock.mockRestore();
    vi.unstubAllEnvs();
  }
});

it('copies the selected source file', async () => {
  runTask.mockImplementation(async (prompt, onEvent) =>
    onEvent({ type: 'complete', data: { success: true, result } })
  );
  const user = await start();
  await user.click(screen.getByRole('button', { name: 'Copy file' }));
  expect(await navigator.clipboard.readText()).toBe('print("hello")');
  expect(screen.getByText('File copied.')).toBeTruthy();
});

it('lets visitors write a custom program under the public request limits', async () => {
  vi.stubEnv('VITE_PUBLIC_DEMO', 'true');
  try {
    runTask.mockImplementation(async (prompt, onEvent) =>
      onEvent({
        type: 'complete',
        data: { success: true, result: { ...result, public_demo: true } },
      })
    );
    const user = userEvent.setup();
    render(<App />);
    expect(screen.getByRole('button', { name: /Build my project/ }).disabled).toBe(true);
    expect(screen.getByLabelText('Your task').maxLength).toBe(1000);
    await user.type(
      screen.getByLabelText('Your task'),
      'Create an expense summary with sample transactions'
    );
    await user.click(screen.getByRole('button', { name: /Build my project/ }));
    expect(runTask.mock.calls[0][0]).toContain('expense summary');
    expect(runTask.mock.calls[0][5]).toBe('custom');
  } finally {
    vi.unstubAllEnvs();
  }
});
it('adds and edits browser files, then exposes the GitHub handoff', async () => {
  runTask.mockImplementation(async (prompt, onEvent) =>
    onEvent({ type: 'complete', data: { success: true, result } })
  );
  const user = await start();
  await user.type(screen.getByLabelText('New file path'), 'utils.py');
  await user.click(screen.getByRole('button', { name: '+ Add file' }));
  await user.type(screen.getByLabelText('Edit file contents'), 'answer = 7');
  expect(screen.getByText(/console below still shows the last executed version/)).toBeTruthy();
  await user.click(screen.getByRole('button', { name: /Export to GitHub/ }));
  expect(screen.getByRole('region', { name: 'GitHub export' })).toBeTruthy();
  expect(screen.getByLabelText('Repository')).toBeTruthy();
});
it('owner can run edits without pretending they were AI reviewed', async () => {
  runTask.mockImplementation(async (prompt, onEvent) =>
    onEvent({ type: 'complete', data: { success: true, result } })
  );
  executeProject.mockResolvedValue({
    code: { files: [{ path: 'main.py', content: 'print(7)' }] },
    execution: { ...execution, stdout: '7' },
    review: {
      feedback: 'Manual execution only. No AI review was requested.',
      mode: 'not_requested',
    },
    success: true,
    duration_ms: 100,
  });
  const user = await start();
  await user.click(screen.getByRole('button', { name: 'Edit files' }));
  await user.clear(screen.getByLabelText('Edit file contents'));
  await user.type(screen.getByLabelText('Edit file contents'), 'print(7)');
  await user.click(screen.getByRole('button', { name: 'Run edited project' }));
  expect(
    await screen.findByText('Manual execution only. No AI review was requested.')
  ).toBeTruthy();
  expect(executeProject).toHaveBeenCalledOnce();
});
