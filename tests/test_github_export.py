from contextlib import redirect_stdout, redirect_stderr
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import requests
from app.tools.github_export import prepare_export, preview, publish, GitHubClient, ExportError, main
from app.models.schemas import CodeResponse, GeneratedFile


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.env=patch.dict(os.environ,{'GITHUB_EXPORT_REPO':'owner/repo'})
        self.env.start();self.addCleanup(self.env.stop)
        self.project=CodeResponse(files=[GeneratedFile(path='main.py',content='print("hello")'),
                                         GeneratedFile(path='src/helpers.py',content='value = 42')])
        self.plan=prepare_export(self.project,'owner/repo')

    def client(self, pr=True):
        client=Mock()
        client.request.side_effect=[{'object':{'sha':'parent'}},{'tree':{'sha':'base-tree'}},{},
                                    {'sha':'new-tree'},{'sha':'new-commit'},{},
                                    {'html_url':'https://github.com/owner/repo/pull/1'}]
        return client

    def test_preview_is_local_scoped_and_omits_content(self):
        result=preview(self.plan)
        self.assertNotIn('content',result['files'][0])
        self.assertTrue(result['branch'].startswith('mini-devin/export-'))
        self.assertTrue(all(f['path'].startswith(result['prefix']+'/') for f in result['files']))
        self.assertEqual(len(result['files'][0]['sha256']),64)

    def test_repo_must_match_explicit_allowlist(self):
        for repo in ['another/repo','https://evil.test/repo','owner/repo/extra']:
            with self.subTest(repo=repo), self.assertRaises(ValueError):prepare_export(self.project,repo)

    def test_unsafe_paths_and_environment_files_rejected(self):
        for path in ['../escape.py','/tmp/escape.py','.env','nested/.git/config','.env.production']:
            project=CodeResponse(files=[GeneratedFile(path=path,content='secret')])
            with self.subTest(path=path),self.assertRaises(ValueError):prepare_export(project,'owner/repo')

    def test_duplicate_conflict_and_empty_projects_rejected(self):
        for paths in [[],['a.py','a.py'],['src','src/a.py']]:
            project=CodeResponse(files=[GeneratedFile(path=p,content='pass') for p in paths])
            with self.subTest(paths=paths),self.assertRaises(ValueError):prepare_export(project,'owner/repo')

    def test_size_and_file_count_limits(self):
        with patch('app.tools.github_export.MAX_BYTES',1),self.assertRaises(ValueError):prepare_export(self.project,'owner/repo')
        with patch('app.tools.github_export.MAX_FILES',1),self.assertRaises(ValueError):prepare_export(self.project,'owner/repo')

    def test_preserves_base_tree_and_parent_and_only_creates_new_ref(self):
        client=self.client()
        result=publish(self.plan,client)
        calls=client.request.call_args_list
        self.assertEqual(calls[2].kwargs['expected'],404)
        tree=calls[3].kwargs['json']
        self.assertEqual(tree['base_tree'],'base-tree')
        self.assertTrue(all(f['path'].startswith(self.plan['prefix']+'/') for f in tree['tree']))
        self.assertEqual(calls[4].kwargs['json']['parents'],['parent'])
        self.assertEqual(calls[5].kwargs['json']['ref'],'refs/heads/'+self.plan['branch'])
        self.assertTrue(all(call.args[0] in ['GET','POST'] for call in calls))
        self.assertEqual(result['commit'],'new-commit')
        self.assertIsNone(result['pull_request'])

    def test_pr_is_draft_and_targets_requested_base(self):
        client=self.client()
        result=publish(self.plan,client,create_pr=True)
        payload=client.request.call_args_list[-1].kwargs['json']
        self.assertTrue(payload['draft'])
        self.assertEqual(payload['base'],'main')
        self.assertEqual(result['pull_request'],'https://github.com/owner/repo/pull/1')

    def test_pr_failure_returns_branch_recovery_information(self):
        client=self.client()
        responses=list(client.request.side_effect);responses[-1]=ExportError('GitHub error')
        client.request.side_effect=responses
        result=publish(self.plan,client,create_pr=True)
        self.assertEqual(result['branch'],self.plan['branch'])
        self.assertIn('warning',result)
        self.assertIn('compare_url',result)

    def test_ref_failure_exposes_safe_recovery_state(self):
        client=self.client()
        responses=list(client.request.side_effect);responses[5]=ExportError('timeout')
        client.request.side_effect=responses
        with self.assertRaises(ExportError) as raised:publish(self.plan,client)
        self.assertEqual(raised.exception.recovery,{'branch':self.plan['branch'],'commit':'new-commit'})

    def test_existing_directory_or_permission_error_prevents_writes(self):
        client=self.client()
        client.request.side_effect=[{'object':{'sha':'parent'}},{'tree':{'sha':'base-tree'}},ExportError('HTTP 200')]
        with self.assertRaises(ExportError):publish(self.plan,client)
        self.assertTrue(all(c.args[0]=='GET' for c in client.request.call_args_list))

    def test_transport_is_fixed_host_bounded_and_does_not_follow_redirects(self):
        session=Mock();session.request.return_value.status_code=200
        session.request.return_value.json.return_value={}
        client=GitHubClient('secret-token',session)
        client.request('GET','/repos/owner/repo')
        call=session.request.call_args
        self.assertEqual(call.args[1],'https://api.github.com/repos/owner/repo')
        self.assertEqual(call.kwargs['timeout'],20)
        self.assertFalse(call.kwargs['allow_redirects'])
        self.assertFalse(session.trust_env)

    def test_transport_errors_do_not_echo_token_or_upstream_body(self):
        for error in [requests.Timeout('secret-token'),requests.ConnectionError('secret-token')]:
            session=Mock();session.request.side_effect=error
            with self.assertRaises(ExportError) as raised:GitHubClient('secret-token',session).request('GET','/test')
            self.assertNotIn('secret-token',str(raised.exception))
        session=Mock();session.request.return_value.status_code=403
        session.request.return_value.text='secret-token'
        with self.assertRaises(ExportError) as raised:GitHubClient('secret-token',session).request('GET','/test')
        self.assertNotIn('secret-token',str(raised.exception))

    def test_cli_defaults_to_preview_without_network_or_token(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'result.json';path.write_text(self.project.model_dump_json())
            output=io.StringIO()
            with patch('app.tools.github_export.GitHubClient') as client,redirect_stdout(output):
                status=main(['--result',str(path),'--repo','owner/repo'])
            self.assertEqual(status,0)
            self.assertEqual(json.loads(output.getvalue())['mode'],'preview')
            client.assert_not_called()

    def test_cli_rejects_pr_without_apply_and_non_object_input(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'result.json';path.write_text('[]')
            with redirect_stderr(io.StringIO()):
                self.assertEqual(main(['--result',str(path),'--repo','owner/repo']),1)
                self.assertEqual(main(['--result',str(path),'--repo','owner/repo','--create-pr']),1)
