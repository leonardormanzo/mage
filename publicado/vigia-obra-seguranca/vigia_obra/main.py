"""CLI: analisa um vídeo de canteiro de obra e reporta não-conformidades de segurança.

Uso:
    python -m vigia_obra.main caminho/para/video.mp4 --interval 5 --output ocorrencias.json

Protocolo de saída (stdout): NDJSON — uma linha JSON por evento, pensado para
ser consumido por um processo pai (frontend local via subprocess). Cada linha
tem um campo "type":

    {"type": "start", "total_frames_estimate": 12, "interval": 5.0, "model": "..."}
    {"type": "progress", "frame_index": 0, "timestamp": "00:00", "ocorrencias": [...]}
    {"type": "error", "frame_index": 3, "message": "..."}
    {"type": "done", "total_ocorrencias": 4, "output_file": "ocorrencias.json", "disclaimer": "..."}

`total_frames_estimate` pode ser `null` quando o vídeo não expõe metadados
confiáveis de duração/fps — trate como "indeterminado" (barra de progresso
indefinida) nesse caso.
"""

import argparse
import json
import sys

import anthropic

from .frame_extractor import estimate_frame_count, extract_frames
from .vision_analyzer import analyze_frame

DISCLAIMER = (
    "Esta análise é assistiva (visão computacional) e NÃO substitui inspeção presencial "
    "de um técnico de segurança do trabalho. Todas as ocorrências abaixo devem ser "
    "revisadas por um responsável do SESMT antes de qualquer ação."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Análise de segurança do trabalho em vídeo de obra.")
    parser.add_argument("video", help="Caminho para o arquivo de vídeo")
    parser.add_argument("--interval", type=float, default=5.0, help="Intervalo entre frames analisados, em segundos (padrão: 5)")
    parser.add_argument("--max-frames", type=int, default=None, help="Limite de frames a analisar (útil para testes)")
    parser.add_argument("--output", default="ocorrencias.json", help="Arquivo JSON de saída (padrão: ocorrencias.json)")
    parser.add_argument("--model", default="claude-opus-5", help="Modelo Claude a usar (padrão: claude-opus-5)")
    parser.add_argument("--effort", default="medium", choices=["low", "medium", "high", "xhigh", "max"], help="Nível de esforço/raciocínio (padrão: medium)")
    return parser.parse_args()


def emit(event: dict) -> None:
    """Escreve uma linha NDJSON em stdout e força o flush (essencial para
    consumo em tempo real por um processo pai que lê linha a linha)."""
    print(json.dumps(event, ensure_ascii=False), flush=True)


def main() -> None:
    args = parse_args()
    client = anthropic.Anthropic()

    total_frames_estimate = estimate_frame_count(args.video, args.interval, args.max_frames)

    emit(
        {
            "type": "start",
            "total_frames_estimate": total_frames_estimate,
            "interval": args.interval,
            "model": args.model,
        }
    )

    all_ocorrencias: list[dict] = []

    for i, frame in enumerate(extract_frames(args.video, args.interval, args.max_frames)):
        try:
            ocorrencias = analyze_frame(client, frame, args.model, args.effort)
        except anthropic.APIStatusError as e:
            emit(
                {
                    "type": "error",
                    "frame_index": i,
                    "timestamp": frame.timestamp_label,
                    "message": f"Erro na API ({e.status_code}): {e.message}",
                }
            )
            continue

        all_ocorrencias.extend(ocorrencias)
        emit(
            {
                "type": "progress",
                "frame_index": i,
                "timestamp": frame.timestamp_label,
                "ocorrencias": ocorrencias,
            }
        )

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(all_ocorrencias, f, ensure_ascii=False, indent=2)

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
