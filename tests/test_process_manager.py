import os
import signal
import subprocess
import sys
import time
import unittest

from core.process_manager import ProcessManager


class ProcessManagerTests(unittest.TestCase):
    def test_cancel_process_terminates_process_group(self):
        script = """
import os, time
pid = os.fork()
if pid == 0:
    time.sleep(30)
else:
    time.sleep(30)
"""
        process = subprocess.Popen(
            [sys.executable, "-c", script],
            start_new_session=True,
        )
        manager = ProcessManager()
        manager.register(process.pid)

        manager.cancel(process.pid)
        deadline = time.time() + 3
        while process.poll() is None and time.time() < deadline:
            time.sleep(0.05)

        self.assertIsNotNone(process.poll())
        self.assertIn(process.pid, manager.active_pids)


if __name__ == "__main__":
    unittest.main()
