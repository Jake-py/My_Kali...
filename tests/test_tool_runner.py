import unittest

from core.tool_runner import CommandWorker


class CommandWorkerTests(unittest.TestCase):
    def test_successful_run_emits_normalized_result(self):
        results = []
        worker = CommandWorker(
            ["printf", "[+] GitHub: https://github.com/red_ice\\n"],
            tool_key="sherlock",
            target="red_ice",
        )
        worker.normalized_signal.connect(results.append)

        worker.run()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].tool, "sherlock")
        self.assertEqual(results[0].records, [{
            "type": "account",
            "url": "https://github.com/red_ice",
        }])


if __name__ == "__main__":
    unittest.main()
