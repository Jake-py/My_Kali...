import unittest

from core.recon_planner import ReconPlanner
from core.recon_profile import ReconLevel
from core.recon_queue import ReconTargetQueue


class ReconPlannerTests(unittest.TestCase):
    def test_planner_selects_only_compatible_tools(self):
        queue = ReconTargetQueue(["example.com"])
        queued_target = queue.pop()
        planner = ReconPlanner()

        plan = planner.plan_target(queued_target, ReconLevel.DEEP, ["nmap", "amass", "sherlock"])

        self.assertEqual([item.tool_key for item in plan], ["nmap", "amass"])
        self.assertTrue(all(item.level == ReconLevel.DEEP for item in plan))

    def test_plan_item_builds_command_for_its_target_and_level(self):
        queue = ReconTargetQueue(["example.com"])
        item = ReconPlanner().plan_target(
            queue.pop(), ReconLevel.EXTENDED, ["amass"]
        )[0]

        command = item.build_command()

        self.assertEqual(command, ["amass", "enum", "-active", "-d", "example.com"])


if __name__ == "__main__":
    unittest.main()