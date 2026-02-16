#!/bin/bash
# Qwen3-TTS ローカルセットアップ (macOS Apple Silicon)
# 使い方: bash local_tts_setup.sh

set -e

echo "=========================================="
echo "  Qwen3-TTS ローカルセットアップ"
echo "  MacBook Pro (Apple Silicon M1-M5)"
echo "=========================================="
echo ""

# Python バージョン確認
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "ERROR: Python が見つかりません"
    echo "brew install python3 でインストールしてください"
    exit 1
fi

PY_VERSION=$($PYTHON_CMD --version 2>&1)
echo "Python: $PY_VERSION"

# venv 作成
VENV_DIR="$(cd "$(dirname "$0")" && pwd)/venv_tts"

if [ ! -d "$VENV_DIR" ]; then
    echo ""
    echo "--- 仮想環境を作成中... ---"
    $PYTHON_CMD -m venv "$VENV_DIR"
    echo "仮想環境: $VENV_DIR"
else
    echo "仮想環境: $VENV_DIR (既存)"
fi

# activate
source "$VENV_DIR/bin/activate"

# pip アップグレード
pip install --upgrade pip -q

# パッケージインストール
echo ""
echo "--- パッケージをインストール中... ---"
pip install -U qwen-tts gradio soundfile numpy -q

echo ""
echo "=========================================="
echo "  セットアップ完了！"
echo ""
echo "  起動コマンド:"
echo "    source $VENV_DIR/bin/activate"
echo "    python3 $(cd "$(dirname "$0")" && pwd)/local_tts.py"
echo ""
echo "  または一発起動:"
echo "    bash $(cd "$(dirname "$0")" && pwd)/local_tts_run.sh"
echo "=========================================="
