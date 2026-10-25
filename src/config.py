"""Opciones disponibles en la app."""

# Tamaños de modelo de Whisper. Más grande = más preciso, pero más lento y pesado.
MODEL_SIZES = {
    "tiny": "Tiny (~75 MB) · muy rápido, precisión básica",
    "base": "Base (~145 MB) · rápido",
    "small": "Small (~480 MB) · buen equilibrio (recomendado en CPU)",
    "medium": "Medium (~1.5 GB) · muy preciso, lento en CPU",
    "large-v3": "Large v3 (~3 GB) · máxima precisión, ideal con GPU",
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
