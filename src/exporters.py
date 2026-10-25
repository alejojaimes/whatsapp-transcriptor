"""Exporta una transcripción a TXT, SRT o VTT."""

from __future__ import annotations

from .transcriber import Segment, Transcription


def _timestamp(seconds: float, sep: str) -> str:
    ms_total = int(round(seconds * 1000))
    h, rem = divmod(ms_total, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def to_txt(t: Transcription, with_timestamps: bool = False) -> str:
    if not with_timestamps:
        return t.text + "\n"
    lines = [f"[{format_clock(s.start)}] {s.text.strip()}" for s in t.segments]
    return "\n".join(lines) + "\n"


def to_srt(segments: list[Segment]) -> str:
    blocks = []
    for i, s in enumerate(segments, start=1):
        blocks.append(
            f"{i}\n{_timestamp(s.start, ',')} --> {_timestamp(s.end, ',')}\n{s.text.strip()}\n"
        )
    return "\n".join(blocks)


def to_vtt(segments: list[Segment]) -> str:
    blocks = ["WEBVTT\n"]
    for s in segments:
        blocks.append(f"{_timestamp(s.start, '.')} --> {_timestamp(s.end, '.')}\n{s.text.strip()}\n")
    return "\n".join(blocks)


def format_clock(seconds: float) -> str:
    """Formato corto para mostrar: m:ss o h:mm:ss."""
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
