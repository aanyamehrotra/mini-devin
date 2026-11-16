import React from 'react';
import { it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import GitHubPanel, { githubHandoff } from './GitHubPanel.jsx';
const files = [{ path: 'main.py', content: 'print(42)' }];
it('prepares a real CLI handoff without contacting GitHub or asking for credentials', async () => {
  const user = userEvent.setup();
  render(<GitHubPanel files={files} />);
  await user.type(screen.getByLabelText('Repository'), 'owner/repo');
  await user.click(screen.getByRole('button', { name: 'Preview GitHub export' }));
  expect(screen.getByText(/No GitHub changes have been made/)).toBeTruthy();
  expect(screen.getByRole('button', { name: 'Download export JSON' })).toBeTruthy();
  expect(githubHandoff(files, 'owner/repo').command).toContain('app.tools.github_export');
  expect(githubHandoff(files, 'owner/repo').command).not.toContain('--apply');
});
it('rejects secret paths, invalid repositories and shell-unsafe branches', () => {
  expect(() => githubHandoff([{ path: '.env', content: 'secret' }], 'owner/repo')).toThrow(
    'secrets'
  );
  expect(() => githubHandoff(files, 'owner/repo;echo')).toThrow('repository');
  expect(() => githubHandoff(files, 'owner/repo', "main'bad")).toThrow('branch');
});
