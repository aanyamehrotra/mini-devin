import subprocess
import sys
import unittest
from app.executor.capture import capture_output, MAX_OUTPUT_BYTES


class CaptureTests(unittest.TestCase):
    def run_code(self, code, timeout=5):
        return capture_output([sys.executable,'-c',code],timeout=timeout)

    def test_both_streams_and_exit_status(self):
        result=self.run_code('import sys; print("hello"); print("error",file=sys.stderr); sys.exit(3)')
        self.assertEqual(result.returncode,3)
        self.assertEqual(result.stdout.strip(),'hello')
        self.assertEqual(result.stderr.strip(),'error')

    def test_flood_is_stopped_and_retained_output_is_bounded(self):
        result=self.run_code('import os\nwhile True: os.write(1,b"x"*65536)')
        self.assertEqual(result.returncode,-2)
        self.assertLessEqual(len(result.stdout.encode()),MAX_OUTPUT_BYTES)
        self.assertIn('OutputLimitExceeded',result.stderr)

    def test_timeout_kills_process(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            self.run_code('import time; time.sleep(10)',timeout=.1)

    def test_invalid_utf8_is_replaced(self):
        result=self.run_code('import os; os.write(1,b"\\xff")')
        self.assertEqual(result.stdout,'\ufffd')
