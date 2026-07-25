"""
Audio utterance module — mock and real (ElevenLabs Scribe v2 Realtime) paths.
"""
import os
import time
import json
import queue
import threading
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

# Mock by default — safe everywhere (tests, Render, fresh clones). The demo
# laptop goes live by putting AUDIO_USE_MOCK=false in its .env; no code edit.
USE_MOCK: bool = os.environ.get("AUDIO_USE_MOCK", "true").strip().lower() \
    not in ("0", "false", "no", "off")
EMPTY: Dict[str, Any] = {"text": "", "speaker": "unknown", "ts": 0.0}

_MOCK_UTTERANCES: List[Dict[str, Any]] = [
    {"text": "Are you guys SOC 2 certified?", "speaker": "prospect", "ts": 252.4},
    {"text": "Is that Type I or Type II?", "speaker": "prospect", "ts": 255.1},
    {"text": "Do you have any fun plans for the weekend?", "speaker": "prospect", "ts": 260.8},
    {"text": "How much does the enterprise tier cost?", "speaker": "prospect", "ts": 268.3},
]
_current_index: int = 0

# --- Real path state ---
_queue: "queue.Queue" = queue.Queue()
_ws_thread_started: bool = False
_session_start: float = 0.0
_benchmark = os.environ.get("AUDIO_BENCHMARK") == "1"
_pending_send_times: Dict[str, float] = {}


def _start_ws_thread() -> None:
    """Starts the background WebSocket thread exactly once."""
    global _ws_thread_started, _session_start
    if _ws_thread_started:
        return
    _ws_thread_started = True
    _session_start = time.time()
    t = threading.Thread(target=_ws_worker, daemon=True)
    t.start()


def _ws_worker() -> None:
    """Runs forever in the background: mic capture + WebSocket send/recv,
    with automatic reconnect on failure. Never raises out of this thread."""
    import base64
    import sounddevice as sd
    import websocket
    import requests

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass
    api_key = os.environ.get("ELEVENLABS_API_KEY", "")

    while True:
        try:
            # Scribe v2 realtime auth: mint a single-use token, pass it as a
            # query parameter; the ws handshake itself takes no api key.
            resp = requests.post(
                "https://api.elevenlabs.io/v1/single-use-token/realtime_scribe",
                headers={"xi-api-key": api_key},
                timeout=10,
            )
            resp.raise_for_status()
            payload = resp.json()
            token = payload.get("token") or payload.get("single_use_token") or ""
            url = (
                "wss://api.elevenlabs.io/v1/speech-to-text/realtime"
                "?model_id=scribe_v2_realtime&sample_rate=16000"
                f"&commit_strategy=vad&token={token}"
            )
            ws = websocket.create_connection(url, timeout=10)

            stop_flag = threading.Event()

            def _on_audio(indata, frames, time_info, status):
                try:
                    ws.send(json.dumps({
                        "message_type": "input_audio_chunk",
                        "audio_base_64": base64.b64encode(bytes(indata)).decode(),
                    }))
                    if _benchmark:
                        _pending_send_times[str(time.time())] = time.time()
                except Exception:
                    stop_flag.set()

            stream = sd.RawInputStream(
                samplerate=16000, channels=1, dtype="int16", blocksize=4000,
                callback=_on_audio
            )
            stream.start()

            while not stop_flag.is_set():
                try:
                    raw = ws.recv()
                except Exception:
                    stop_flag.set()
                    break
                if not raw:
                    continue
                if os.environ.get("AUDIO_DEBUG") == "1":
                    print(f"[audio] recv={str(raw)[:220]}")
                try:
                    msg = json.loads(raw)
                except Exception:
                    continue

                msg_type = msg.get("message_type", msg.get("type", ""))
                if msg_type in ("partial_transcript", "session_started"):
                    continue  # discard partials per spec
                if msg_type in ("committed_transcript", "final_transcript"):
                    text = msg.get("text", "")
                    if not text:
                        continue
                    speaker = msg.get("speaker", "unknown") or "unknown"
                    ts = time.time() - _session_start
                    _queue.put({"text": text, "speaker": speaker, "ts": ts})
                    if _benchmark and _pending_send_times:
                        oldest = min(_pending_send_times.values())
                        latency_ms = (time.time() - oldest) * 1000
                        print(f"[audio] benchmark latency_ms={latency_ms:.1f}")
                        _pending_send_times.clear()

            stream.stop()
            stream.close()
            ws.close()

        except Exception as e:
            print(f"[audio] ws error, reconnecting: {e}")

        time.sleep(1)  # backoff before reconnect


def get_utterance() -> Dict[str, Any]:
    """
    Retrieves the next utterance. Mock path replays a hardcoded list.
    Real path pops a committed transcript from the streaming queue, or
    returns EMPTY immediately if none is available.
    """
    global _current_index
    try:
        if USE_MOCK:
            if _current_index < len(_MOCK_UTTERANCES):
                utterance = _MOCK_UTTERANCES[_current_index]
                _current_index += 1
            else:
                utterance = EMPTY
        else:
            _start_ws_thread()
            try:
                utterance = _queue.get_nowait()
            except queue.Empty:
                utterance = EMPTY

        print(f"[audio] out={utterance['text']}")
        return utterance

    except Exception as e:
        print(f"[audio] Error retrieving utterance: {e}")
        print(f"[audio] out={EMPTY['text']}")
        return EMPTY


if __name__ == "__main__":
    for i in range(6):
        result = get_utterance()
        print(f"Call {i + 1} result: {result}")