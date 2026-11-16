// @vitest-environment node
import { it, expect } from 'vitest';
import { unzipSync, strFromU8 } from 'fflate';
import { projectZip } from './project.js';

it('downloads exact multi-file content as a valid ZIP', () => {
  const files = [
    { path: 'main.py', content: 'print("café")\n' },
    { path: 'src/helpers.py', content: 'value = 42\n' },
  ];
  const archive = unzipSync(projectZip(files));
  expect(Object.keys(archive)).toEqual(files.map((file) => file.path));
  files.forEach((file) => expect(strFromU8(archive[file.path])).toBe(file.content));
});
it.each(['../secret', '/etc/password', 'src/../../secret', 'C:\\secret', 'src//file'])(
  'rejects unsafe download path %s',
  (path) => {
    expect(() => projectZip([{ path, content: 'x' }])).toThrow('unsafe');
  }
);
it('rejects duplicates and overlarge projects', () => {
  expect(() =>
    projectZip([
      { path: 'main.py', content: 'x' },
      { path: 'main.py', content: 'y' },
    ])
  ).toThrow('duplicate');
  expect(() => projectZip([{ path: 'main.py', content: 'x'.repeat(1024 * 1024 + 1) }])).toThrow(
    'limit'
  );
});

it('rejects file/directory conflicts before creating a ZIP', () => {
  expect(() =>
    projectZip([
      { path: 'src', content: 'not a directory' },
      { path: 'src/main.py', content: 'print(1)' },
    ])
  ).toThrow('path conflict');
});
