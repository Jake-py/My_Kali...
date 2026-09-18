import unittest

from core.recon_controller import ReconController
from core.recon_profile import ReconLevel
from core.tool_adapter import NormalizedResult


class ReconControllerTests(unittest.TestCase):
    def test_controller_runs_plan_and_schedules_discovered_target(self):
        controller = ReconController(
            level=ReconLevel.EXTENDED,
            tool_keys=["nmap", "amass", "sherlock"],
        )
        self.assertEqual(controller.seed(["example.com"]), 2)

        first = controller.next_item()
        self.assertIsNotNone(first)
        self.assertEqual(first.target.target.normalized_value, "example.com")
        self.assertEqual(first.level, ReconLevel.EXTENDED)

        scheduled = controller.complete(NormalizedResult(
            first.tool_key,
            first.target.target.normalized_value,
            [{"type": "domain", "value": "api.example.com"}],
        ))

        self.assertEqual(scheduled, 2)
        self.assertEqual(controller.next_item().target.target.normalized_value, "example.com")

    def test_duplicate_result_does_not_schedule_duplicate_work(self):
        controller = ReconController(tool_keys=["nmap", "amass"])
        controller.seed(["example.com"])
        item = controller.next_item()
        result = NormalizedResult(item.tool_key, "example.com", [
            {"type": "domain", "value": "api.example.com"},
        ])
        controller.complete(result)

        api_items = [
            pending for pending in controller._pending
            if pending.target.target.normalized_value == "api.example.com"
        ]
        self.assertEqual(len(api_items), 2)


if __name__ == "__main__":
    unittest.main()