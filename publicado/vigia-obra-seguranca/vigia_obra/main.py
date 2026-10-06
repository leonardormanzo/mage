"""CLI: analisa um vídeo de canteiro de obra e reporta não-conformidades de segurança.

Suporta Google Gemini (gratuito via Google AI Studio), Anthropic Claude ou Modo Demo local com OpenCV.
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
from .frame_extractor import estimate_frame_count, extract_frames

DISCLAIMER = (
    "Esta análise é assistiva (visão computacional) e NÃO substitui inspeção presencial "
    "de um técnico de segurança do trabalho. Todas as ocorrências abaixo devem ser "
    "revisadas por um responsável do SESMT antes de qualquer ação."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Análise de segurança do trabalho em vídeo de obra.")
    parser.add_argument("video", help="Caminho para o arquivo de vídeo")
    parser.add_argument("--interval", type=float, default=5.0, help="Intervalo entre frames analisados, em segundos")
    parser.add_argument("--max-frames", type=int, default=None, help="Limite de frames a analisar")
    parser.add_argument("--output", default="ocorrencias.json", help="Arquivo JSON de saída")
    parser.add_argument("--model", default="gemini-3.5-flash", help="Modelo de IA")
    parser.add_argument("--effort", default="medium", choices=["low", "medium", "high", "xhigh", "max"], help="Nível de esforço/raciocínio")
    parser.add_argument("--provider", default="", help="Provedor: gemini, anthropic ou demo")
    parser.add_argument("--demo", action="store_true", help="Modo demonstração/teste local")
    return parser.parse_args()


def emit(event: dict) -> None:
    print(json.dumps(event, ensure_ascii=False), flush=True)


def main() -> None:
    args = parse_args()

    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "").strip()
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()

    is_demo = args.demo or (not gemini_key and not anthropic_key)
    provider = args.provider.lower() if args.provider else ("gemini" if gemini_key else ("anthropic" if anthropic_key else "demo"))

    gemini_client = None
    anthropic_client = None
    engine_name = "Modo Demonstração (OpenCV Local)"

    if not is_demo and provider == "gemini" and gemini_key and "sua-chave" not in gemini_key:
        try:
            from google import genai
            gemini_client = genai.Client(api_key=gemini_key)
            from .gemini_analyzer import analyze_frame_gemini
            engine_name = f"Google Gemini ({args.model})"
        except Exception as err:
            emit({"type": "error", "message": f"Falha ao iniciar cliente Google Gemini ({err}). Alternando para demonstração local."})
            is_demo = True

    elif not is_demo and provider == "anthropic" and anthropic_key and "sua-chave" not in anthropic_key:
        try:
            import anthropic
            anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
            from .vision_analyzer import analyze_frame
            engine_name = f"Anthropic Claude ({args.model})"
        except Exception as err:
            emit({"type": "error", "message": f"Falha ao iniciar cliente Anthropic ({err}). Alternando para demonstração local."})
            is_demo = True
    else:
        is_demo = True

    try:
        total_frames_estimate = estimate_frame_count(args.video, args.interval, args.max_frames)
    except Exception:
        total_frames_estimate = None

    emit(
        {
            "type": "start",
            "total_frames_estimate": total_frames_estimate,
            "interval": args.interval,
            "model": engine_name,
            "is_demo": is_demo,
        }
    )

    all_ocorrencias: list[dict] = []

    try:
        frames_iter = extract_frames(args.video, args.interval, args.max_frames)
        for i, frame in enumerate(frames_iter):
            if is_demo:
                ocorrencias = analyze_frame_demo(frame, frame_index=i)
            elif gemini_client:
                from .gemini_analyzer import analyze_frame_gemini
                model_name = args.model if "gemini" in args.model else "gemini-2.0-flash"
                ocorrencias = analyze_frame_gemini(gemini_client, frame, model=model_name)
            elif anthropic_client:
                from .vision_analyzer import analyze_frame
                model_name = args.model if "claude" in args.model else "claude-sonnet-5"
                ocorrencias = analyze_frame(anthropic_client, frame, model_name, args.effort)
            else:
                ocorrencias = analyze_frame_demo(frame, frame_index=i)

            all_ocorrencias.extend(ocorrencias)
            emit(
                {
                    "type": "progress",
                    "frame_index": i,
                    "timestamp": frame.timestamp_label,
                    "ocorrencias": ocorrencias,
                }
            )
    except Exception as e:
        emit(
            {
                "type": "error",
                "message": f"Erro ao processar vídeo: {e}",
            }
        )

    try:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(all_ocorrencias, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    emit(
        {
            "type": "done",
            "total_ocorrencias": len(all_ocorrencias),
            "output_file": args.output,
            "disclaimer": DISCLAIMER,
        }
    )


if __name__ == "__main__":
    main()
