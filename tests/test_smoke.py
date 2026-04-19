import unittest

from src.main import process_astro_request
from src.house_rules import RULE_HANDLERS, apply_house_rules
from src.question_parser import parse_question
from src.query_engine import run_prasna_query_from_coords


PAYLOAD = {
    "datetime": {
        "year": 2026,
        "month": 2,
        "day": 22,
        "hour": 10,
        "minute": 0,
        "second": 0,
        "utc_offset": 5.5,
    },
    "location": {"latitude": 28.6139, "longitude": 77.2090, "altitude": 0.0},
    "ayanamsa": "LAHIRI",
}


class SmokeTests(unittest.TestCase):
    def test_question_parser_detects_marriage(self):
        parsed = parse_question("Will I get married soon?")
        self.assertEqual(parsed["query_topic"], "marriage")
        self.assertEqual(parsed["query_house"], 7)

    def test_process_astro_request_returns_core_sections(self):
        result = process_astro_request(PAYLOAD, query_house=7)
        self.assertIn("positions", result)
        self.assertIn("house_judgment", result)
        self.assertIn("tajaka_yogas", result)
        self.assertIn("sincerity_check", result)
        self.assertIn("timing_estimate", result)
        self.assertIn("Ascendant", result["positions"])
        self.assertIn(result["house_judgment"]["karyasiddhi_percent"], {25, 50, 75, 100})

    def test_query_engine_smoke(self):
        result = run_prasna_query_from_coords(
            28.6139,
            77.2090,
            "2026-02-22",
            "10:00:00",
            "marriage",
        )
        self.assertEqual(result["query_topic"], "marriage")
        self.assertEqual(result["query_house"], 7)
        self.assertIn("summary", result)
        self.assertIn("house_judgment", result)
        self.assertEqual(result["errors"], [])

    def test_query_engine_allows_house_override(self):
        result = run_prasna_query_from_coords(
            28.6139,
            77.2090,
            "2026-02-22",
            "10:00:00",
            "wealth",
            query_house_override=7,
        )
        self.assertEqual(result["query_topic"], "wealth")
        self.assertEqual(result["query_house"], 7)

    def test_house_rule_registry_contains_supported_handlers(self):
        for house in [2, 3, 4, 5, 6, 7, 9, 10]:
            self.assertIn(house, RULE_HANDLERS)

    def test_apply_house_rules_returns_structured_output(self):
        result = process_astro_request(PAYLOAD, query_house=7)
        rules = apply_house_rules(
            7,
            result["positions"],
            result["house_lords"],
            result["tajaka_yogas"],
            result["house_judgment"],
        )
        self.assertIn("specific_verdict", rules)
        self.assertIn("specific_factors", rules)
        self.assertIsInstance(rules["specific_factors"], list)


if __name__ == "__main__":
    unittest.main()
