"""Envoltorio sobre faster-whisper."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


@dataclass
class Segment:
    start: float
    end: float
    text: str


@dataclass
class Transcription:
    language: str
    language_probability: float
    duration: float
    segments: list[Segment] = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join(s.text.strip() for s in self.segments).strip()


# Orden de preferencia: primero lo más rápido con buena calidad.
# Las GPU antiguas (p. ej. GTX 10xx) no soportan float16 eficiente,
# así que se cae a int8 o float32 según lo que la tarjeta permita.
CUDA_COMPUTE_PREFERENCE = ["float16", "int8_float16", "int8", "int8_float32", "float32"]
CPU_COMPUTE_PREFERENCE = ["int8", "int8_float32", "float32"]


def pick_compute_type(supported: set[str], preference: list[str]) -> str:
    for ct in preference:
        if ct in supported:
            return ct
    return "float32"


def detect_device() -> tuple[str, str]:
    """Devuelve (device, compute_type) según el hardware disponible."""
    try:
        import ctranslate2

        if ctranslate2.get_cuda_device_count() > 0:
            supported = set(ctranslate2.get_supported_compute_types("cuda"))
            return "cuda", pick_compute_type(supported, CUDA_COMPUTE_PREFERENCE)
        supported = set(ctranslate2.get_supported_compute_types("cpu"))
        return "cpu", pick_compute_type(supported, CPU_COMPUTE_PREFERENCE)
    except Exception:
        # int8 en CPU: mucho más rápido y con poca pérdida de calidad.
        return "cpu", "int8"


def load_model(model_size: str, device: str | None = None, compute_type: str | None = None):
    """Carga el modelo. La primera vez lo descarga (queda en caché local)."""
    from faster_whisper import WhisperModel

    auto_device, auto_compute = detect_device()
    return WhisperModel(
        model_size,
        device=device or auto_device,
        compute_type=compute_type or auto_compute,
    )


def transcribe(
    model,
    audio_path: str | Path,
    language: str | None = None,
    vad_filter: bool = True,
    on_progress: Callable[[float], None] | None = None,
) -> Transcription:
    """Transcribe un archivo de audio.

    on_progress recibe un valor entre 0 y 1 a medida que avanza.
    """
    segments_iter, info = model.transcribe(
        str(audio_path),
        language=None if language in (None, "auto") else language,
        vad_filter=vad_filter,  # salta silencios: más rápido y menos "alucinaciones"
        beam_size=5,
    )

    result = Transcription(
        language=info.language,
        language_probability=info.language_probability,
        duration=info.duration,
    )

    # faster-whisper genera los segmentos de forma perezosa:
    # la transcripción ocurre mientras recorremos el iterador.
    for seg in segments_iter:
        result.segments.append(Segment(start=seg.start, end=seg.end, text=seg.text))
        if on_progress and info.duration:
            on_progress(min(seg.end / info.duration, 1.0))

    if on_progress:
        on_progress(1.0)
    return result
