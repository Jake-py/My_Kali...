import unittest

from core.tool_adapter import ToolAdapter, ToolState, tool_registry
from core.target_engine import TargetType, target_engine
from core.recon_profile import ReconLevel


class ToolAdapterTests(unittest.TestCase):
    def test_missing_binary_has_explicit_health_state(self):
        adapter = ToolAdapter("missing", {
            "name": "Missing", "binary": "red-kali-tool-that-does-not-exist",
            "category": "network", "cmd_builder": lambda target, options, sudo: ["echo", target],
        })
        self.assertEqual(adapter.health_check().state, ToolState.MISSING)

    def test_adapter_delegates_command_builder(self):
        adapter = ToolAdapter("test", {
            "name": "Test", "binary": "echo", "category": "network",
            "cmd_builder": lambda target, options, sudo: ["echo", target, str(sudo)],
        })
        self.assertEqual(adapter.build_command("example.com", {}, True), ["echo", "example.com", "True"])
        self.assertIn("domain", adapter.supported_targets)

    def test_nmap_profiles_change_the_command_depth(self):
        from core.tool_adapter import tool_registry
        adapter = tool_registry.get("nmap")
        quick = adapter.build_command("192.168.1.1", {}, True, ReconLevel.QUICK)
        extended = adapter.build_command("192.168.1.1", {}, True, ReconLevel.EXTENDED)
        deep = adapter.build_command("192.168.1.1", {}, True, ReconLevel.DEEP)
        self.assertIn("--top-ports", quick)
        self.assertIn("100", quick)
        self.assertIn("--top-ports", extended)
        self.assertIn("1000", extended)
        self.assertIn("-sV", extended)
        self.assertNotIn("-p-", extended)
        self.assertIn("-p-", deep)
        self.assertIn("-sV", deep)

    def test_amass_deep_profile_adds_ip_enrichment(self):
        from core.tool_adapter import tool_registry
        adapter = tool_registry.get("amass")
        extended = adapter.build_command("example.com", {}, False, ReconLevel.EXTENDED)
        deep = adapter.build_command("example.com", {}, False, ReconLevel.DEEP)
        self.assertNotIn("-ip", extended)
        self.assertIn("-ip", deep)

    def test_nmap_output_is_normalized_into_hosts_and_services(self):
        adapter = tool_registry.get("nmap")
        result = adapter.normalize(
            "192.168.1.1",
            "Nmap scan report for router (192.168.1.1)\n"
            "22/tcp open ssh OpenSSH 9.0\n",
        )
        self.assertEqual(result.records[0], {
            "type": "host", "host": "router", "ip": "192.168.1.1"
        })
        self.assertEqual(result.records[1]["type"], "service")
        self.assertEqual(result.records[1]["port"], 22)

    def test_account_output_extracts_found_urls(self):
        adapter = tool_registry.get("sherlock")
        result = adapter.normalize("red_ice", "[+] GitHub: https://github.com/red_ice\n")
        self.assertEqual(result.records, [{
            "type": "account", "url": "https://github.com/red_ice"
        }])

    def test_adapter_checks_target_compatibility(self):
        adapter = ToolAdapter("test", {
            "name": "Test", "binary": "echo", "category": "network",
            "cmd_builder": lambda target, options, sudo: ["echo", target],
        })
        self.assertTrue(adapter.supports(target_engine.parse("192.168.1.1")))
        self.assertFalse(adapter.supports(target_engine.parse("user@example.com")))


if __name__ == "__main__":
    unittest.main()
