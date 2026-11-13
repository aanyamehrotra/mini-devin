"""Explicit, preview-first GitHub export to a fresh branch and project directory."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import quote
import uuid

import requests
from app.executor.workspace import resolve_project_files
from app.models.schemas import CodeResponse

API = 'https://api.github.com'
MAX_FILES = 100
MAX_BYTES = 1024 * 1024


class ExportError(RuntimeError):
    def __init__(self, message, *, recovery=None):
        super().__init__(message)
        self.recovery = recovery



def prepare_export(project, repo, base='main', title='Export generated project'):
    allowed = os.getenv('GITHUB_EXPORT_REPO', '')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9][A-Za-z0-9_.-]*', repo) or repo.casefold() != allowed.casefold():
        raise ValueError('Repository must match the configured GITHUB_EXPORT_REPO')
    if (not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]{0,199}', base)
            or any(part in base for part in ('..', '//', '@{')) or base.endswith(('/', '.', '.lock'))):
        raise ValueError('Invalid base branch')
    if not title.strip() or len(title) > 200 or '\n' in title or '\r' in title:
        raise ValueError('Title must be a single line of 1 to 200 characters')
    if not 1 <= len(project.files) <= MAX_FILES:
        raise ValueError('Export requires 1 to 100 files')
    root = Path('/__mini_devin_export__').resolve()
    resolved = resolve_project_files(root, project.files)
    total = sum(len(content.encode('utf-8')) for _, content in resolved)
    if total > MAX_BYTES:
        raise ValueError('Export exceeds the 1 MiB content limit')
    identifier = uuid.uuid4().hex
    prefix = f'generated/{identifier}'
    files = []
    for target, content in resolved:
        relative = target.relative_to(root)
        if any(p.casefold() == '.git' or p.casefold() == '.env'
               or p.casefold().startswith('.env.') and p.casefold() != '.env.example'
               for p in relative.parts):
            raise ValueError('Git metadata and environment secrets cannot be exported')
        files.append({'path': f'{prefix}/{relative.as_posix()}', 'content': content,
                      'bytes': len(content.encode('utf-8')),
                      'sha256': hashlib.sha256(content.encode('utf-8')).hexdigest()})
    return {'repo': repo, 'base': base, 'title': title.strip(),
            'branch': f'mini-devin/export-{identifier}', 'prefix': prefix, 'files': files}


def preview(plan):
    return {**{key: value for key, value in plan.items() if key != 'files'},
            'files': [{key: value for key, value in file.items() if key != 'content'} for file in plan['files']]}


class GitHubClient:
    def __init__(self, token, session=None):
        if not token:
            raise ValueError('GITHUB_EXPORT_TOKEN is required for --apply')
        self.session = session or requests.Session()
        self.session.trust_env = False
        self.headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json',
                        'X-GitHub-Api-Version': '2026-03-10'}

    def request(self, method, path, expected=200, **kwargs):
        try:
            response = self.session.request(method, API + path, headers=self.headers,
                                            timeout=20, allow_redirects=False, **kwargs)
        except requests.RequestException:
            raise ExportError('GitHub request failed; verify remote state before retrying') from None
        if response.status_code != expected:
            raise ExportError(f'GitHub returned HTTP {response.status_code}')
        try:
            return response.json()
        except ValueError:
            raise ExportError('GitHub returned invalid JSON') from None


def publish(plan, client, *, create_pr=False):
    # Plans are internal objects from prepare_export, not accepted as external input.
    repo = '/repos/' + '/'.join(quote(part, safe='') for part in plan['repo'].split('/'))
    head = client.request('GET', repo + '/git/ref/heads/' + quote(plan['base'], safe=''))
    parent = head['object']['sha']
    commit = client.request('GET', repo + '/git/commits/' + quote(parent, safe=''))
    # Refuse even an unlikely UUID-directory collision before creating objects.
    client.request('GET', repo + '/contents/' + plan['prefix'], expected=404,
                   params={'ref': plan['base']})
    tree = client.request('POST', repo + '/git/trees', expected=201, json={
        'base_tree': commit['tree']['sha'],
        'tree': [{'path': file['path'], 'mode': '100644', 'type': 'blob',
                  'content': file['content']} for file in plan['files']],
    })
    created = client.request('POST', repo + '/git/commits', expected=201, json={
        'message': plan['title'], 'tree': tree['sha'], 'parents': [parent],
    })
    try:
        client.request('POST', repo + '/git/refs', expected=201,
                       json={'ref': 'refs/heads/' + plan['branch'], 'sha': created['sha']})
    except ExportError as error:
        raise ExportError('Branch creation did not confirm success; verify remote state before retrying',
                          recovery={'branch': plan['branch'], 'commit': created['sha']}) from None
    result = {'repo': plan['repo'], 'branch': plan['branch'], 'commit': created['sha'],
              'compare_url': f'https://github.com/{plan["repo"]}/compare/{quote(plan["base"],safe="")}...{quote(plan["branch"],safe="")}',
              'pull_request': None}
    if create_pr:
        try:
            pr = client.request('POST', repo + '/pulls', expected=201, json={
                'title': plan['title'], 'head': plan['branch'], 'base': plan['base'], 'draft': True,
                'body': 'Generated project exported for human review.\n\n'
                        'Export does not certify tests, execution safety or correctness.\n'
                        f'Files are isolated under `{plan["prefix"]}/`.',
            })
            result['pull_request'] = pr['html_url']
        except (ExportError, KeyError, TypeError):
            result['warning'] = 'Branch created, but draft PR failed. Use compare_url; do not blindly re-export.'
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--result', required=True, help='JSON from /chat or a CodeResponse object')
    parser.add_argument('--repo', required=True)
    parser.add_argument('--base', default='main')
    parser.add_argument('--title', default='Export generated project')
    parser.add_argument('--apply', action='store_true', help='Explicitly create a branch/commit on GitHub')
    parser.add_argument('--create-pr', action='store_true', help='Also open a draft PR (requires --apply)')
    args = parser.parse_args(argv)
    try:
        if args.create_pr and not args.apply:
            raise ValueError('--create-pr requires --apply')
        path = Path(args.result)
        if path.stat().st_size > 2 * MAX_BYTES:
            raise ValueError('Result JSON is too large')
        data = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            raise ValueError('Result must be a JSON object')
        project = CodeResponse.model_validate(data.get('code', data), strict=True)
        plan = prepare_export(project, args.repo, args.base, args.title)
        if not args.apply:
            output = {'mode': 'preview', **preview(plan)}
        else:
            output = publish(plan, GitHubClient(os.getenv('GITHUB_EXPORT_TOKEN')), create_pr=args.create_pr)
        print(json.dumps(output, indent=2))
        return 0
    except ExportError as error:
        print(json.dumps({'error': str(error), 'recovery': error.recovery}), file=sys.stderr)
        return 1
    except (OSError, ValueError, TypeError, KeyError, requests.RequestException):
        # Never print input, raw upstream bodies or transport errors containing credentials.
        print('Export failed. Check input/configuration and remote branch state before retrying.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
