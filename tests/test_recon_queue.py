import unittest

from core.recon_queue import ReconTargetQueue
from core.tool_adapter import NormalizedResult


class ReconTargetQueueTests(unittest.TestCase):
    def test_initial_target_and_results_are_fifo_and_unique(self):
        queue = ReconTargetQueue(["example.com"])
        result = NormalizedResult("amass", "example.com", [
            {"type": "domain", "value": "api.example.com"},
            {"type": "domain", "value": "API.EXAMPLE.COM"},
            {"type": "line", "value": "not a target"},
        ])

        added = queue.add_result(result)

        self.assertEqual([target.normalized_value for target in added], ["api.example.com"])
        self.assertEqual([item.target.normalized_value for item in queue.drain()], [
            "example.com", "api.example.com"
        ])

    def test_queue_extracts_nmap_ip_and_account_url(self):
        queue = ReconTargetQueue()
        result = NormalizedResult("nmap", "example.com", [
            {"type": "host", "host": "router", "ip": "192.168.1.1"},
        ])
        queue.add_result(result)

        self.assertIn("192.168.1.1", queue)
        self.assertEqual(queue.pop().target.normalized_value, "192.168.1.1")


if __name__ == "__main__":
    unittest.main()