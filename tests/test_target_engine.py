import unittest

from core.target_engine import TargetType, target_engine


class TargetEngineTests(unittest.TestCase):
    def test_classifies_and_normalizes_common_targets(self):
        cases = {
            "192.168.001.1": TargetType.UNKNOWN,
            "192.168.1.1": TargetType.IP,
            "192.168.1.10/24": TargetType.CIDR,
            "Example.COM.": TargetType.DOMAIN,
            "https://Example.COM/path#fragment": TargetType.URL,
            "User@Example.COM": TargetType.EMAIL,
            "+998 90 123 45 67": TargetType.PHONE,
            "red_ice": TargetType.USERNAME,
            "@RedIce": TargetType.SOCIAL_USERNAME,
        }
        for raw, expected_type in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(target_engine.parse(raw).target_type, expected_type)

    def test_normalizes_url_and_identity(self):
        self.assertEqual(target_engine.parse("https://Example.COM/path#x").normalized_value,
                         "https://example.com/path")
        self.assertEqual(target_engine.parse("@RedIce").normalized_value, "redice")


if __name__ == "__main__":
    unittest.main()
