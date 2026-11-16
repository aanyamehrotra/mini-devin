import unittest
from app.evaluation.runner import check_result, summarize, tasks


class EvaluationTests(unittest.TestCase):
    def test_review_approval_does_not_override_wrong_output(self):
        task = tasks()[0]
        result = {'execution': {'success': True, 'stdout': 'wrong'}, 'code': {'files': [{'path': 'main.py'}]}, 'review': {'success': True}}
        self.assertFalse(check_result(task, result)['passed'])
        result['execution']['stdout'] = task['expected_stdout']+'\n'
        self.assertTrue(check_result(task, result)['passed'])
        result['execution']['success'] = False
        self.assertFalse(check_result(task, result)['passed'])

    def test_multifile_task_requires_both_modules(self):
        task = next(task for task in tasks() if task['id']=='log-analyzer')
        result = {'execution': {'success': True, 'stdout': task['expected_stdout']}, 'code': {'files': [{'path':'main.py'}]}}
        self.assertFalse(check_result(task,result)['passed'])
        result['code']['files'].append({'path':'analyzer.py'})
        self.assertTrue(check_result(task,result)['passed'])

    def test_summary_includes_failures_and_attempts(self):
        summary=summarize([{'passed':True,'seconds':2,'attempts':1},{'passed':False,'seconds':4,'attempts':3}])
        self.assertEqual(summary,{'tasks':2,'passed':1,'success_rate':.5,'median_seconds':3,'total_attempts':4})
        self.assertEqual(summarize([])['tasks'],0)
