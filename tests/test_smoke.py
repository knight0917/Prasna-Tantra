import unittest
from unittest.mock import patch

import requests

from src.main import process_astro_request
from src.house_rules import RULE_HANDLERS, apply_house_rules
from src.groq_question_parser import _apply_common_derived_house_correction, _sanitize_result, parse_question_with_groq
from src.question_parser import parse_question
from src.query_engine import run_prasna_query_from_coords
from src.tajaka_yogas import detect_tajaka_yogas


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
        self.assertFalse(parsed.get("needs_clarification", False))

    def test_question_parser_flags_vague_question_for_clarification(self):
        parsed = parse_question("what now")
        self.assertTrue(parsed.get("needs_clarification"))
        self.assertEqual(parsed["confidence"], "low")

    def test_groq_parser_sanitizes_derived_house_result(self):
        parsed = _sanitize_result(
            {
                "query_house": 2,
                "query_topic": "career",
                "confidence": "high",
                "needs_clarification": False,
                "rephrased": "Will my child get a job?",
                "reasoning": "Child is 5th; profession is 10th from 5th.",
                "derived_house_used": True,
                "base_house": 5,
                "derived_from": "10th from 5th = 2nd house.",
            },
            "Will my child get a job?",
        )
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["query_house"], 2)
        self.assertTrue(parsed["derived_house_used"])

    def test_groq_parser_corrects_common_derived_house_result(self):
        parsed = _sanitize_result(
            {
                "query_house": 10,
                "query_topic": "career",
                "confidence": "high",
                "needs_clarification": False,
                "rephrased": "Will my child get a job?",
                "reasoning": "Natural career house.",
                "derived_house_used": False,
            },
            "Will my child get a job?",
        )
        corrected = _apply_common_derived_house_correction(parsed, "Will my child get a job?")
        self.assertEqual(corrected["query_house"], 2)
        self.assertEqual(corrected["query_topic"], "career")
        self.assertTrue(corrected["derived_house_used"])

    def test_groq_parser_corrects_brother_marriage_derivation(self):
        parsed = _sanitize_result(
            {
                "query_house": 7,
                "query_topic": "marriage",
                "confidence": "high",
                "needs_clarification": False,
                "rephrased": "Will my brother get married?",
                "reasoning": "Natural marriage house.",
                "derived_house_used": False,
            },
            "Will my brother get married?",
        )
        corrected = _apply_common_derived_house_correction(parsed, "Will my brother get married?")
        self.assertEqual(corrected["query_house"], 9)
        self.assertEqual(corrected["query_topic"], "marriage")
        self.assertTrue(corrected["derived_house_used"])

    def test_groq_parser_corrects_more_book_derived_examples(self):
        examples = [
            ("What about my mother's longevity?", 11, "longevity"),
            ("Will my spouse get money?", 8, "wealth"),
            ("Will my child get married?", 11, "marriage"),
            ("Will my father recover his health?", 2, "illness"),
            ("Will my friend's lost article be found?", 12, "wealth"),
        ]
        for question, house, topic in examples:
            parsed = _sanitize_result(
                {
                    "query_house": 1,
                    "query_topic": topic,
                    "confidence": "high",
                    "needs_clarification": False,
                    "rephrased": question,
                    "reasoning": "Needs derived houses.",
                    "derived_house_used": False,
                },
                question,
            )
            corrected = _apply_common_derived_house_correction(parsed, question)
            self.assertEqual(corrected["query_house"], house, question)
            self.assertEqual(corrected["query_topic"], topic, question)
            self.assertTrue(corrected["derived_house_used"], question)

    def test_groq_parser_returns_none_when_api_fails(self):
        with patch("src.groq_question_parser.requests.post", side_effect=requests.RequestException("network down")):
            parsed = parse_question_with_groq("Will I get married?", api_key="test-key")
        self.assertIsNone(parsed)

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
        for house in [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]:
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
        self.assertIn("source_rules", rules)
        self.assertIsInstance(rules["specific_factors"], list)
        self.assertIsInstance(rules["source_rules"], list)

    def test_house_judgment_carries_source_rules(self):
        result = process_astro_request(PAYLOAD, query_house=7)
        self.assertIn("source_rules", result["house_judgment"])
        self.assertIsInstance(result["house_judgment"]["source_rules"], list)

    def test_new_house_rules_return_book_basis(self):
        for house in [8, 11, 12]:
            result = process_astro_request(PAYLOAD, query_house=house)
            judgment = result["house_judgment"]
            self.assertIn("specific_verdict", judgment)
            self.assertIn("source_rules", judgment)
            self.assertIsInstance(judgment["source_rules"], list)

    def test_timing_is_withheld_when_no_perfection_exists(self):
        result = process_astro_request(PAYLOAD, query_house=7)
        self.assertFalse(result["house_judgment"]["ithasala_present"])
        self.assertIn("error", result["timing_estimate"])
        self.assertIn("Timing withheld", result["timing_estimate"]["error"])

    def test_tajaka_detection_ignores_nodes(self):
        yogas = detect_tajaka_yogas(
            [
                {"name": "Mars", "longitude": 10.0, "speed_deg_per_day": 0.5},
                {"name": "Venus", "longitude": 12.0, "speed_deg_per_day": 1.2},
                {"name": "Rahu", "longitude": 11.0, "speed_deg_per_day": -0.05},
                {"name": "Ketu", "longitude": 191.0, "speed_deg_per_day": -0.05},
            ]
        )
        detected_names = set()
        for key in ("ithasala", "easarapha", "naktha", "yamaya", "kamboola"):
            for item in yogas[key]:
                detected_names.update(str(item))
        self.assertNotIn("Rahu", detected_names)
        self.assertNotIn("Ketu", detected_names)


if __name__ == "__main__":
    unittest.main()
