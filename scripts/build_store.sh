#!/usr/bin/env bash
# Provision the retrieval vector store. Run this ONCE per environment before the
# app serves traffic — locally, in CI, or as a Render build/pre-deploy step.
# It is a standalone build job; the app never triggers it.
#
#   scripts/build_store.sh              # build if missing (idempotent)
#   scripts/build_store.sh --force      # always rebuild
set -euo pipefail
cd "$(dirname "$0")/.."

MODE="--if-missing"
if [ "${1:-}" = "--force" ]; then MODE="--force"; fi

python -m pip install -r requirements.txt
python ingest.py "$MODE"
