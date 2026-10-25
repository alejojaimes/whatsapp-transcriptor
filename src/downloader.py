"""Descarga de modelos de Hugging Face con progreso visible.

faster-whisper descarga el modelo en silencio. Aquí hacemos la descarga
nosotros en un hilo aparte y medimos cuántos bytes van llegando al disco,
comparándolos con el tamaño total que informa Hugging Face. Así el progreso
funciona igual sin importar la versión de huggingface_hub.
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Callable

# Los mismos archivos que descarga faster-whisper.
ALLOW_PATTERNS = [
    "config.json",
    "preprocessor_config.json",
    "model.bin",
    "tokenizer.json",
    "vocabulary.*",
]


@dataclass
class DownloadProgress:
    downloaded: int  # bytes
    total: int  # bytes (0 si no se conoce)
    speed: float  # bytes por segundo

    @property
    def fraction(self) -> float:
        return min(self.downloaded / self.total, 1.0) if self.total else 0.0


def repo_id_for(model_size: str) -> str:
    """'small' -> 'Systran/faster-whisper-small'."""
    if "/" in model_size:
        return model_size
    try:
        from faster_whisper.utils import _MODELS

        return _MODELS[model_size]
    except Exception:
        return f"Systran/faster-whisper-{model_size}"


def cached_model_path(model_size: str) -> str | None:
    """Ruta local del modelo si ya está descargado; None si no."""
    from huggingface_hub import snapshot_download

    try:
        return snapshot_download(
            repo_id_for(model_size), allow_patterns=ALLOW_PATTERNS, local_files_only=True
        )
    except Exception:
        return None


def remote_size(repo_id: str) -> int:
    """Tamaño total, en bytes, de los archivos que vamos a descargar."""
    from huggingface_hub import HfApi

    info = HfApi().model_info(repo_id, files_metadata=True)
    return sum(
        s.size or 0
        for s in info.siblings or []
        if any(fnmatch(s.rfilename, p) for p in ALLOW_PATTERNS)
    )


def repo_cache_dir(repo_id: str) -> Path:
    from huggingface_hub import constants

    return Path(constants.HF_HUB_CACHE) / ("models--" + repo_id.replace("/", "--"))


def dir_size(path: Path) -> int:
    """Suma el tamaño real de los archivos (sin contar los enlaces simbólicos)."""
    total = 0
    for root, _, files in os.walk(path):
        for name in files:
            p = os.path.join(root, name)
            try:
                if not os.path.islink(p):
                    total += os.path.getsize(p)
            except OSError:
                pass  # el archivo se movió mientras lo medíamos
    return total


def download_model(
    model_size: str,
    on_progress: Callable[[DownloadProgress], None] | None = None,
    poll_interval: float = 0.5,
    _download: Callable[[str], str] | None = None,
) -> str:
    """Descarga el modelo y devuelve su ruta local.

    on_progress se llama cada `poll_interval` segundos desde el hilo que
    invoca esta función (necesario para que Streamlit pueda pintar la barra).
    """
    from huggingface_hub import snapshot_download

    repo_id = repo_id_for(model_size)
    cache_dir = repo_cache_dir(repo_id)

    try:
        total = remote_size(repo_id)
    except Exception:
        total = 0  # sin tamaño total: mostramos solo los MB descargados

    download = _download or (
        lambda rid: snapshot_download(rid, allow_patterns=ALLOW_PATTERNS)
    )
    result: dict = {}

    def worker():
        try:
            result["path"] = download(repo_id)
        except Exception as e:  # se relanza en el hilo principal
            result["error"] = e

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    # Si hay una descarga a medias de antes, los bytes ya en disco cuentan.
    last_bytes, last_time, speed = dir_size(cache_dir), time.monotonic(), 0.0
    while thread.is_alive():
        thread.join(poll_interval)
        now_bytes, now = dir_size(cache_dir), time.monotonic()
        if now > last_time:
            instant = max(now_bytes - last_bytes, 0) / (now - last_time)
            speed = instant if speed == 0 else 0.7 * speed + 0.3 * instant  # suavizado
        last_bytes, last_time = now_bytes, now
        if on_progress:
            shown = min(now_bytes, total) if total else now_bytes
            on_progress(DownloadProgress(shown, total, speed))

    if "error" in result:
        raise result["error"]
    if on_progress:
        final = total or dir_size(cache_dir)
        on_progress(DownloadProgress(final, final, 0.0))
    return result["path"]


def human_bytes(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit in ("B", "KB") else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} GB"
