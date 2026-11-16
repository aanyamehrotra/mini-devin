import unittest
from tests import test_orchestration
from app.agents.manager import run_agent


class TimingTests(unittest.TestCase):
    setUp=test_orchestration.OrchestrationTests.setUp

    def test_stage_timings_match_actual_executed_stages(self):
        result=run_agent('hello')
        self.assertEqual([item['stage'] for item in result['timings']],['plan','generate','execute','review'])
        self.assertTrue(all(item['duration_ms']>=0 for item in result['timings']))
        self.assertEqual([item['attempt'] for item in result['timings']],[1,1,1,1])
