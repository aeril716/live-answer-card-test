"""Minimal usage example for trigger.should_fire() / reset_call().

Run from the repo root: python context/trigger_example.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import trigger

trigger.reset_call()  # call at the start of every sales call

call = [
    {"text": "How was your weekend?", "speaker": "prospect", "ts": 10.0},
    {"text": "Are you SOC 2 certified?", "speaker": "prospect", "ts": 14.2},
    {"text": "Are you SOC 2 compliant?", "speaker": "prospect", "ts": 55.9},
]

for utterance in call:
    decision = trigger.should_fire(utterance)
    if decision["fire"]:
        print("-> fire card for:", decision["question"])
    else:
        print("-> stay silent:", decision["reason"])
