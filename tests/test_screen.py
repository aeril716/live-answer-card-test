import io
import os
import sys
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import screen

FULL_CARD = {
    "keywords": ["SOC 2 — YES", "TYPE II", "NDA → REPORT"],
    "detail": "SOC 2 Type II, renewed March 2026 after an external audit.",
    "source": "security-overview.md §1.1",
    "confidence": 0.91,
}


def _capture(card):
    buf = io.StringIO()
    with redirect_stdout(buf):
        screen.render(card)
    return buf.getvalue()


class RenderTests(unittest.TestCase):
    def test_full_card_renders_keywords_and_source(self):
        output = _capture(FULL_CARD)
        self.assertIn("SOC 2 — YES", output)
        self.assertIn("TYPE II", output)
        self.assertIn("NDA → REPORT", output)
        self.assertIn("security-overview.md §1.1", output)
        self.assertIn("out=rendered", output)

    def test_below_threshold_renders_empty_state(self):
        output = _capture({**FULL_CARD, "confidence": 0.4})
        self.assertIn("out=empty", output)
        self.assertNotIn("TYPE II", output)

    def test_confidence_exactly_threshold_renders(self):
        output = _capture({**FULL_CARD, "confidence": 0.6})
        self.assertIn("out=rendered", output)

    def test_empty_dict_does_not_raise_and_shows_empty_state(self):
        output = _capture({})
        self.assertIn("out=empty", output)

    def test_missing_keys_shows_empty_state(self):
        output = _capture({"keywords": ["A"], "confidence": 0.9})
        self.assertIn("out=empty", output)

    def test_five_keywords_renders_only_three(self):
        card = {**FULL_CARD, "keywords": ["A", "B", "C", "D", "E"]}
        output = _capture(card)
        for kw in ("A", "B", "C"):
            self.assertIn(kw, output)
        for kw in ("D", "E"):
            self.assertNotIn(kw, output)

    def test_boolean_confidence_is_invalid(self):
        output = _capture({**FULL_CARD, "confidence": True})
        self.assertIn("out=empty", output)

    def test_control_characters_in_keyword_select_empty_state(self):
        card = {**FULL_CARD, "keywords": ["bad\nkeyword", "B", "C"]}
        output = _capture(card)
        self.assertIn("out=empty", output)

    def test_non_dict_card_does_not_raise(self):
        for bad_card in (None, "not a card", 123, ["a", "list"]):
            with self.subTest(bad_card=bad_card):
                output = _capture(bad_card)
                self.assertIn("out=empty", output)

    def test_diagnostic_line_format(self):
        output = _capture(FULL_CARD)
        lines = [line for line in output.splitlines() if line.startswith("[screen]")]
        self.assertEqual(len(lines), 1)
        self.assertRegex(lines[0], r"^\[screen\] in=conf=.+ out=(rendered|empty)$")


if __name__ == "__main__":
    unittest.main()
