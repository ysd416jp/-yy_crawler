#!/bin/bash
# Qwen3-TTS ローカル起動 (ワンコマンド)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/venv_tts/bin/activate"
python3 "$SCRIPT_DIR/local_tts.py" "$@"
