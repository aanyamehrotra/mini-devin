import { zipSync, strToU8 } from 'fflate';

export function projectZip(files) {
  const entries = {};
  let bytes = 0;
  for (const file of files) {
    const path = file.path.replaceAll('\\', '/');
    if (
      !path ||
      path.startsWith('/') ||
      path.includes(':') ||
      path.split('/').some((part) => !part || part === '..' || part === '.') ||
      Object.hasOwn(entries, path)
    )
      throw new Error('This project contains an unsafe or duplicate file path.');
    const content = strToU8(file.content);
    bytes += content.length;
    if (bytes > 1024 * 1024 || Object.keys(entries).length >= 100)
      throw new Error('This project exceeds the download limit.');
    Object.defineProperty(entries, path, { value: content, enumerable: true });
  }
  return zipSync(entries, { level: 0 });
}

export function downloadProject(files) {
  const url = URL.createObjectURL(new Blob([projectZip(files)], { type: 'application/zip' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'mini-devin-project.zip';
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
