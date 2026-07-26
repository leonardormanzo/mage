"""Extração de frames de um vídeo a intervalos regulares, usando OpenCV."""

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import cv2


@dataclass
class Frame:
    timestamp_seconds: float
    timestamp_label: str  # formato mm:ss
    png_bytes: bytes


def _format_timestamp(seconds: float) -> str:
    total_seconds = int(round(seconds))
    minutes, secs = divmod(total_seconds, 60)
    return f"{minutes:02d}:{secs:02d}"


def estimate_frame_count(video_path: str, interval_seconds: float, max_frames: int | None = None) -> int | None:
    """Estima quantos frames serão analisados, para exibir progresso no front.

    Retorna None se o vídeo não expõe metadados confiáveis de duração/fps.
    """
    capture = cv2.VideoCapture(str(video_path))
    try:
        if not capture.isOpened():
            return None
        fps = capture.get(cv2.CAP_PROP_FPS)
        total_frames = capture.get(cv2.CAP_PROP_FRAME_COUNT)
        if not fps or fps <= 0 or not total_frames or total_frames <= 0:
            return None
        frame_step = max(1, int(round(fps * interval_seconds)))
        estimate = int(total_frames - 1) // frame_step + 1
        if max_frames is not None:
            estimate = min(estimate, max_frames)
        return estimate
    finally:
        capture.release()


def extract_frames(video_path: str, interval_seconds: float, max_frames: int | None = None) -> Iterator[Frame]:
    """Percorre o vídeo e retorna um frame a cada `interval_seconds`.

    Usa OpenCV diretamente (sem dependência externa de ffmpeg).
    """
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"Vídeo não encontrado: {video_path}")

    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise RuntimeError(f"Não foi possível abrir o vídeo: {video_path}")

    fps = capture.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 30.0  # fallback razoável quando o metadado não está disponível

    frame_step = max(1, int(round(fps * interval_seconds)))

    frame_index = 0
    emitted = 0
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break

            if frame_index % frame_step == 0:
                timestamp_seconds = frame_index / fps
                success, buffer = cv2.imencode(".png", frame)
                if not success:
                    frame_index += 1
                    continue

                yield Frame(
                    timestamp_seconds=timestamp_seconds,
                    timestamp_label=_format_timestamp(timestamp_seconds),
                    png_bytes=buffer.tobytes(),
                )
                emitted += 1
                if max_frames is not None and emitted >= max_frames:
                    break

            frame_index += 1
    finally:
        capture.release()
