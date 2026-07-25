#!/usr/bin/env bash
# Run the app locally with the REAL microphone/ElevenLabs audio path.
# The deployed Render app can never do this — cloud servers have no mic —
# so this is how you demo live listening: on your own laptop.
#
# Requires ELEVENLABS_API_KEY set in .env (see .env.example). AUDIO_USE_MOCK
# is forced to false here so you don't need to edit .env for it.
#
#   scripts/run_local_live.sh
set -euo pipefail
cd "$(dirname "$0")/.."

python -m pip install -r requirements.txt
AUDIO_USE_MOCK=false streamlit run app.py
