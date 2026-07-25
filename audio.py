"""
Module for simulating the retrieval of audio utterances.
Provides a mock implementation for testing purposes.
"""

from typing import Dict, Any

USE_MOCK: bool = True

EMPTY: Dict[str, Any] = {"text": "", "speaker": "unknown", "ts": 0.0}

_MOCK_UTTERANCES = [
    {"text": "Are you guys SOC 2 certified?", "speaker": "prospect", "ts": 252.4},
    {"text": "Is that Type I or Type II?", "speaker": "prospect", "ts": 255.1},
    {"text": "Did you have a good weekend?", "speaker": "prospect", "ts": 260.0},
    {"text": "How much does it cost?", "speaker": "prospect", "ts": 265.5}
]

_index: int = 0


def get_utterance() -> Dict[str, Any]:
    """
    Retrieves the next utterance from the mock data or returns an empty utterance.
    
    Returns:
        Dict[str, Any]: A dictionary containing utterance details (text, speaker, ts).
    """
    global _index
    try:
        if USE_MOCK and _index < len(_MOCK_UTTERANCES):
            utterance = _MOCK_UTTERANCES[_index]
            _index += 1
        else:
            utterance = EMPTY
            
        print(f"[audio] out={utterance['text']}")
        return utterance
    except Exception as e:
        # Catch unexpected errors to ensure the system gracefully degrades to EMPTY
        print(f"[error] Failed to get utterance: {e}")
        return EMPTY


if __name__ == "__main__":
    for i in range(1, 7):
        print(f"--- Call {i} ---")
        result = get_utterance()
        print("Returned:", result)