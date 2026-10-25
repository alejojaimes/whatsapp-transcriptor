"""Opciones disponibles en la app."""

# Tamaños de modelo de Whisper. Más grande = más preciso, pero más lento y pesado.
MODEL_SIZES = {
    "tiny": "Tiny · pruebas rápidas",
    "base": "Base · rápido",
    "small": "Small · equilibrado",
    "medium": "Medium · preciso",
    "large-v3": "Large v3 · máxima calidad",
}

# Tamaño aproximado de descarga, para mostrarlo como ayuda.
MODEL_DOWNLOAD = {
    "tiny": "~75 MB",
    "base": "~145 MB",
    "small": "~480 MB",
    "medium": "~1.5 GB",
    "large-v3": "~3 GB",
}
DEFAULT_MODEL = "small"

# "auto" deja que Whisper detecte el idioma.
LANGUAGES = {
    "auto": "Detectar automáticamente",
    "es": "Español",
    "en": "Inglés",
    "pt": "Portugués",
    "fr": "Francés",
    "it": "Italiano",
    "de": "Alemán",
}
DEFAULT_LANGUAGE = "es"

# Formatos aceptados. faster-whisper decodifica con PyAV (FFmpeg incluido),
# así que los .opus/.ogg de WhatsApp funcionan sin convertir.
AUDIO_EXTENSIONS = ["opus", "ogg", "mp3", "m4a", "wav", "aac", "flac", "webm", "mp4", "mpeg"]
