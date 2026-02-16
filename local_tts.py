"""
Qwen3-TTS ローカル版 — MacBook Pro (Apple Silicon) 対応
使い方: python3 local_tts.py [--model 0.6B|1.7B] [--share]
"""

import argparse
import sys
import tempfile

import gradio as gr
import numpy as np
import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel


# ==================================================
# デバイス & dtype 自動検出
# ==================================================
def detect_device():
    if torch.cuda.is_available():
        name = torch.cuda.get_device_name(0)
        cap = torch.cuda.get_device_capability()[0]
        dtype = torch.bfloat16 if cap >= 8 else torch.float16
        attn = "flash_attention_2" if cap >= 8 else "sdpa"
        print(f"GPU: {name} (CUDA, compute capability {cap})")
        return "cuda:0", dtype, attn

    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        print(f"GPU: Apple Silicon (MPS)")
        # MPS は float16 が安定。bfloat16 は一部演算で未対応の場合あり
        return "mps", torch.float16, "sdpa"

    print("WARNING: GPU が見つかりません。CPU で動作します（低速）")
    return "cpu", torch.float32, "sdpa"


# ==================================================
# メイン
# ==================================================
def main():
    parser = argparse.ArgumentParser(description="Qwen3-TTS ローカル版")
    parser.add_argument("--model", default="1.7B", choices=["0.6B", "1.7B"],
                        help="モデルサイズ (default: 1.7B)")
    parser.add_argument("--share", action="store_true",
                        help="公開URL (gradio.live) を発行する")
    parser.add_argument("--port", type=int, default=7860,
                        help="ポート番号 (default: 7860)")
    args = parser.parse_args()

    model_size = args.model
    device, dtype, attn_impl = detect_device()

    print(f"\nモデル: {model_size} | Device: {device} | Dtype: {dtype}")
    print(f"Attention: {attn_impl}\n")

    # --- モデル読み込み ---
    print("--- CustomVoice モデル読み込み中... ---")
    model_custom = Qwen3TTSModel.from_pretrained(
        f"Qwen/Qwen3-TTS-12Hz-{model_size}-CustomVoice",
        device_map=device,
        dtype=dtype,
        attn_implementation=attn_impl,
    )
    print("CustomVoice OK\n")

    print("--- Base モデル読み込み中... ---")
    model_base = Qwen3TTSModel.from_pretrained(
        f"Qwen/Qwen3-TTS-12Hz-{model_size}-Base",
        device_map=device,
        dtype=dtype,
        attn_implementation=attn_impl,
    )
    print("Base OK\n")

    model_design = None
    if model_size == "1.7B":
        print("--- VoiceDesign モデル読み込み中... ---")
        model_design = Qwen3TTSModel.from_pretrained(
            "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
            device_map=device,
            dtype=dtype,
            attn_implementation=attn_impl,
        )
        print("VoiceDesign OK\n")

    print("全モデル読み込み完了\n")

    # ==================================================
    # Gradio UI
    # ==================================================
    SPEAKERS = [
        "Vivian", "Serena", "Uncle_Fu", "Dylan",
        "Eric", "Ryan", "Aiden", "Ono_Anna", "Sohee",
    ]
    LANGUAGES = {
        "日本語": "Japanese",
        "英語": "English",
        "中国語": "Chinese",
        "韓国語": "Korean",
        "ドイツ語": "German",
        "フランス語": "French",
    }

    def voice_clone(text, language, ref_audio, ref_text):
        if not text.strip():
            raise gr.Error("読み上げテキストを入力してください")
        if ref_audio is None:
            raise gr.Error("参照音声をアップロードしてください")
        if not ref_text.strip():
            raise gr.Error("参照音声のテキストを入力してください")
        lang = LANGUAGES.get(language, "Japanese")
        wavs, sr = model_base.generate_voice_clone(
            text=text, language=lang,
            ref_audio=ref_audio, ref_text=ref_text,
        )
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        sf.write(tmp.name, wavs[0], sr)
        return tmp.name

    def tts_generate(text, speaker, language):
        if not text.strip():
            raise gr.Error("テキストを入力してください")
        lang = LANGUAGES.get(language, "Japanese")
        wavs, sr = model_custom.generate_custom_voice(
            text=text, language=lang, speaker=speaker,
        )
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        sf.write(tmp.name, wavs[0], sr)
        return tmp.name

    def voice_design_fn(text, language, instruct_text):
        if model_design is None:
            raise gr.Error("VoiceDesign は 1.7B モデルのみ対応です")
        if not text.strip():
            raise gr.Error("テキストを入力してください")
        if not instruct_text.strip():
            raise gr.Error("声質の説明を入力してください")
        lang = LANGUAGES.get(language, "Japanese")
        wavs, sr = model_design.generate_voice_design(
            text=text, language=lang, instruct=instruct_text,
        )
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        sf.write(tmp.name, wavs[0], sr)
        return tmp.name

    # --- UI 構築 ---
    with gr.Blocks(
        title="Qwen3-TTS ボイスクローン",
        theme=gr.themes.Soft(primary_hue="blue", neutral_hue="slate"),
    ) as demo:
        gr.Markdown("# Qwen3-TTS 音声生成 (ローカル版)")
        gr.Markdown(f"モデル: **{model_size}** | デバイス: **{device}**")

        # === ボイスクローン ===
        with gr.Tab("ボイスクローン"):
            gr.Markdown("**mp3/wav をアップ → テキストを入力 → その声で喋る**")
            clone_ref_audio = gr.Audio(
                label="① 参照音声 (3秒以上の mp3/wav)",
                type="filepath",
            )
            clone_ref_text = gr.Textbox(
                label="② 参照音声のテキスト",
                placeholder="例: こんにちは、今日はいい天気ですね。",
                lines=2,
            )
            gr.Markdown("---")
            clone_text = gr.Textbox(
                label="③ 読み上げたいテキスト",
                placeholder="クローンした声で読み上げたい内容...",
                lines=4,
                value="こんにちは。この声は、アップロードされた音声からクローンされたものです。",
            )
            clone_lang = gr.Dropdown(
                choices=list(LANGUAGES.keys()), value="日本語", label="言語",
            )
            clone_btn = gr.Button("クローン音声を生成", variant="primary", size="lg")
            clone_output = gr.Audio(label="生成結果", type="filepath")
            clone_btn.click(
                voice_clone,
                [clone_text, clone_lang, clone_ref_audio, clone_ref_text],
                clone_output,
            )

        # === TTS 読み上げ ===
        with gr.Tab("TTS 読み上げ"):
            gr.Markdown("プリセット音声でテキストを読み上げます")
            tts_text = gr.Textbox(
                label="テキスト", lines=5,
                value="こんにちは。Qwen3-TTSのテストです。",
            )
            with gr.Row():
                tts_speaker = gr.Dropdown(
                    choices=SPEAKERS, value="Ono_Anna", label="音声",
                )
                tts_lang = gr.Dropdown(
                    choices=list(LANGUAGES.keys()), value="日本語", label="言語",
                )
            tts_btn = gr.Button("音声を生成", variant="primary", size="lg")
            tts_output = gr.Audio(label="生成結果", type="filepath")
            tts_btn.click(tts_generate, [tts_text, tts_speaker, tts_lang], tts_output)

        # === ボイスデザイン (1.7B のみ) ===
        if model_design is not None:
            with gr.Tab("ボイスデザイン"):
                gr.Markdown("自然言語で声質を指定して音声を生成します")
                design_text = gr.Textbox(
                    label="読み上げテキスト", lines=4,
                    value="今日はいい天気ですね。散歩に行きましょう。",
                )
                design_lang = gr.Dropdown(
                    choices=list(LANGUAGES.keys()), value="日本語", label="言語",
                )
                design_desc = gr.Textbox(
                    label="声質の説明 (英語推奨)", lines=3,
                    value="A young Japanese woman with a gentle and warm voice.",
                )
                design_btn = gr.Button("デザイン生成", variant="primary", size="lg")
                design_output = gr.Audio(label="生成結果", type="filepath")
                design_btn.click(
                    voice_design_fn,
                    [design_text, design_lang, design_desc],
                    design_output,
                )

        gr.Markdown("---")
        gr.Markdown("Powered by [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS)")

    # 起動
    print("=" * 60)
    print(f"  ブラウザで http://localhost:{args.port} を開いてください")
    if args.share:
        print("  公開URL (gradio.live) も発行します")
    print("=" * 60 + "\n")

    demo.launch(
        server_name="0.0.0.0",
        server_port=args.port,
        share=args.share,
    )


if __name__ == "__main__":
    main()
