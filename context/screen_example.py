"""Minimal usage example for screen.render()."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import screen

card = {
    "keywords": ["SOC 2 — YES", "TYPE II", "NDA → REPORT"],
    "detail": "SOC 2 Type II, renewed March 2026 after an external audit.",
    "source": "security-overview.md §1.1",
    "confidence": 0.91,
}

screen.render(card)
