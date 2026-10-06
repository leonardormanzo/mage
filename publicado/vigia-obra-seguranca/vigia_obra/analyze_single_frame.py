"""CLI para análise de um único frame capturado em tempo real (webcam ou câmera de canteiro).

Suporta Google Gemini (grátis via Google AI Studio), Anthropic Claude ou Modo Demo local.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
load_dotenv()

from .demo_analyzer import analyze_frame_demo
from .frame_extractor import Frame


def parse_args():
    parser = argparse.ArgumentParser(description="Análise em tempo real de frame de câmera.")
    parser.add_argument("image", help="Caminho para o arquivo de imagem do frame")
    parser.add_argument("--demo", action="store_true", help="Modo demonstração/teste local")
    parser.add_argument("--timestamp", default="", help="Timestamp da captura")
    parser.add_argument("--frame-index", type=int, default=0, help="Índice sequencial do frame")
    parser.add_argument("--model", default="gemini-3.5-flash", help="Modelo de IA")
    parser.add_argument("--effort", default="medium", help="Nível de raciocínio")
    parser.add_argument("--provider", default="", help="Provedor (gemini, anthropic ou demo)")
    return parser.parse_args()


def main():
    args = parse_args()
    image_path = Path(args.image)
    if not image_path.exists():
        print(json.dumps({"error": f"Imagem não encontrada: {args.image}"}))
        sys.exit(1)

    with open(image_path, "rb") as f:
        png_bytes = f.read()

    ts = args.timestamp or "00:00"
    frame = Frame(timestamp_seconds=0.0, timestamp_label=ts, png_bytes=png_bytes)

    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "").strip()
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()

    is_demo = args.demo or (not gemini_key and not anthropic_key)
    provider = args.provider.lower() if args.provider else ("gemini" if gemini_key else ("anthropic" if anthropic_key else "demo"))

    ocorrencias = []
    engine_name = "Modo Demo Local"

    if not is_demo and provider == "gemini" and gemini_key and "sua-chave" not in gemini_key:
        try:
            from google import genai
            from .gemini_analyzer import analyze_frame_gemini

            from google.genai import types
            http_opts = types.HttpOptions(
                timeout=10000,
                retry_options=types.HttpRetryOptions(attempts=1),
            )
            client = genai.Client(api_key=gemini_key, http_options=http_opts)
            model_name = args.model if "gemini" in args.model else "gemini-flash-lite-latest"
            ocorrencias = analyze_frame_gemini(client, frame, model=model_name)
            if any("OpenCV Local" in o.get("risco", "") for o in ocorrencias):
                engine_name = "OpenCV Local (Fallback Cota Gemini)"
                is_demo = True
            else:
                engine_name = f"Google Gemini ({model_name})"
        except Exception as e:
            print(f"[Gemini Exception Fallback] {e}", file=sys.stderr)
            ocorrencias = analyze_frame_demo(frame, frame_index=args.frame_index)
            engine_name = "OpenCV Local (Fallback Cota Gemini)"
            is_demo = True
    elif not is_demo and provider == "anthropic" and anthropic_key and "sua-chave" not in anthropic_key:
        try:
            import anthropic
            from .vision_analyzer import analyze_frame

            client = anthropic.Anthropic(api_key=anthropic_key)
            model_name = args.model if "claude" in args.model else "claude-sonnet-5"
            ocorrencias = analyze_frame(client, frame, model_name, args.effort)
            engine_name = f"Claude Vision ({model_name})"
        except Exception as e:
            print(f"[Anthropic Exception Fallback] {e}", file=sys.stderr)
            ocorrencias = analyze_frame_demo(frame, frame_index=args.frame_index)
            is_demo = True
    else:
        ocorrencias = analyze_frame_demo(frame, frame_index=args.frame_index)
        is_demo = True

    print(json.dumps({
        "timestamp": ts,
        "ocorrencias": ocorrencias,
        "is_demo": is_demo,
        "engine": engine_name
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
