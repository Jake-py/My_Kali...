import unittest

from core.recon_correlation import ReconCorrelator
from core.tool_adapter import NormalizedResult


class ReconCorrelationTests(unittest.TestCase):
    def test_correlator_groups_and_deduplicates_related_evidence(self):
        correlator = ReconCorrelator()

        result_a = NormalizedResult(
            "amass",
            "example.com",
            [
                {"type": "domain", "value": "api.example.com"},
                {"type": "domain", "value": "api.example.com"},
                {"type": "account", "url": "https://github.com/example"},
            ],
        )
        result_b = NormalizedResult(
            "sherlock",
            "example.com",
            [
                {"type": "account", "url": "https://github.com/example"},
                {"type": "account", "url": "https://twitter.com/example"},
            ],
        )

        summary_a = correlator.ingest(result_a)
        summary_b = correlator.ingest(result_b)

        self.assertEqual(summary_a["by_type"]["domain"], 1)
        self.assertEqual(summary_b["by_type"]["account"], 2)
        self.assertEqual(correlator.tree["example.com"]["account"]["https://github.com/example"], 2)
        self.assertEqual(len(correlator.all_evidence()), 4)

    def test_correlator_report_contains_overview(self):
        correlator = ReconCorrelator()
        correlator.ingest(NormalizedResult(
            "nmap",
            "10.0.0.1",
            [{"type": "host", "ip": "10.0.0.1"}, {"type": "service", "port": 80, "protocol": "tcp", "service": "http"}],
        ))

        report = correlator.report()
        self.assertIn("summary", report)
        self.assertIn("tree", report)
        self.assertEqual(report["summary"]["total_evidence"], 2)
        self.assertIn("10.0.0.1", report["tree"])


if __name__ == "__main__":
    unittest.main()
