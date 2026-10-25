"""Interfaz web con Streamlit.

Ejecutar con:  streamlit run app.py
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from src import __version__
from src.config import (
    AUDIO_EXTENSIONS,
    DEFAULT_LANGUAGE,
    DEFAULT_MODEL,
    LANGUAGES,
    MODEL_SIZES,
)
from src.downloader import DownloadProgress, cached_model_path, download_model, human_bytes
from src.exporters import format_clock, to_srt, to_txt, to_vtt
from src.transcriber import detect_device, load_model, transcribe

LOGO = Path(__file__).parent / "assets" / "logo.png"
st.set_page_config(page_title="Transcriptor", page_icon=str(LOGO), layout="centered")


@st.cache_resource(show_spinner=False)
def get_model(model_path: str):
    """El modelo se carga una sola vez y se reutiliza entre transcripciones."""
    return load_model(model_path)


def ensure_model(model_size: str) -> str:
    """Devuelve la ruta local del modelo; si no está, lo descarga con barra de progreso."""
    path = cached_model_path(model_size)
    if path:
        return path

    bar = st.progress(0.0, text=f"Preparando descarga del modelo «{model_size}»…")

    def show(p: DownloadProgress):
        speed = f" · {human_bytes(p.speed)}/s" if p.speed else ""
        if p.total:
            text = (
                f"Descargando modelo «{model_size}»: "
                f"{human_bytes(p.downloaded)} de {human_bytes(p.total)} ({p.fraction:.0%}){speed}"
            )
            bar.progress(p.fraction, text=text)
        else:
            bar.progress(0.0, text=f"Descargando modelo «{model_size}»: {human_bytes(p.downloaded)}{speed}")

    try:
        path = download_model(model_size, on_progress=show)
    except Exception as e:
        bar.empty()
        st.error(f"No se pudo descargar el modelo: {e}")
        st.stop()

    bar.progress(1.0, text=f"Modelo «{model_size}» descargado ✓ (solo se descarga una vez)")
    return path


# ---------- Barra lateral: opciones ----------
with st.sidebar:
    st.header("Opciones")
    model_size = st.selectbox(
        "Modelo",
        options=list(MODEL_SIZES),
        index=list(MODEL_SIZES).index(DEFAULT_MODEL),
        format_func=lambda k: MODEL_SIZES[k],
    )
    language = st.selectbox(
        "Idioma del audio",
        options=list(LANGUAGES),
        index=list(LANGUAGES).index(DEFAULT_LANGUAGE),
        format_func=lambda k: LANGUAGES[k],
    )
    vad = st.toggle(
        "Saltar silencios (VAD)",
        value=True,
        help="Ignora partes sin voz. Acelera y evita texto inventado en silencios.",
    )
    timestamps_in_txt = st.toggle("Tiempos en el .txt", value=False)

    device, compute = detect_device()
    st.caption(f"Dispositivo: **{device.upper()}** ({compute}) · v{__version__}")

# ---------- Contenido principal ----------
st.logo(str(LOGO), size="large")

col_logo, col_title = st.columns([1, 6], vertical_alignment="center")
col_logo.image(str(LOGO), width=72)
col_title.title("Transcriptor")
st.write(
    "Convierte audios a texto en tu propia computadora, gratis y sin enviar nada a internet. "
    "Funciona con notas de voz de WhatsApp (.opus / .ogg), MP3, M4A, WAV y más."
)

files = st.file_uploader(
    "Sube uno o varios audios",
    type=AUDIO_EXTENSIONS,
    accept_multiple_files=True,
)

if files and st.button("Transcribir", type="primary", use_container_width=True):
    model_path = ensure_model(model_size)
    with st.spinner(f"Cargando modelo «{model_size}» en {device.upper()}…"):
        model = get_model(model_path)

    results = {}
    for f in files:
        progress = st.progress(0.0, text=f"Analizando {f.name}…")
        suffix = Path(f.name).suffix or ".audio"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(f.getbuffer())
            tmp_path = Path(tmp.name)

        def on_progress(p: float, name=f.name, bar=progress):
            bar.progress(p, text=f"Transcribiendo {name}… {p:.0%}")

        try:
            t = transcribe(model, tmp_path, language=language, vad_filter=vad, on_progress=on_progress)
            results[f.name] = t
            progress.progress(1.0, text=f"{f.name} ✓ · {format_clock(t.duration)} de audio")
        except Exception as e:  # audio corrupto, formato raro, etc.
            progress.empty()
            st.error(f"No se pudo transcribir **{f.name}**: {e}")
        finally:
            tmp_path.unlink(missing_ok=True)

    st.session_state["results"] = results

# Los resultados se guardan en session_state para que no se pierdan
# al pulsar un botón de descarga (Streamlit vuelve a ejecutar el script).
for name, t in st.session_state.get("results", {}).items():
    st.divider()
    st.subheader(name)
    st.caption(
        f"Duración: {format_clock(t.duration)} · "
        f"Idioma: {t.language} ({t.language_probability:.0%})"
    )

    st.text_area("Texto", t.text, height=200, key=f"text_{name}")

    with st.expander("Ver por segmentos con tiempos"):
        for s in t.segments:
            st.markdown(f"`{format_clock(s.start)}` {s.text.strip()}")

    stem = Path(name).stem
    c1, c2, c3 = st.columns(3)
    c1.download_button("⬇️ .txt", to_txt(t, timestamps_in_txt), f"{stem}.txt", key=f"txt_{name}")
    c2.download_button("⬇️ .srt", to_srt(t.segments), f"{stem}.srt", key=f"srt_{name}")
    c3.download_button("⬇️ .vtt", to_vtt(t.segments), f"{stem}.vtt", key=f"vtt_{name}")
