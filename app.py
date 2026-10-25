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
    MODEL_DOWNLOAD,
    MODEL_SIZES,
)
from src.downloader import DownloadProgress, cached_model_path, download_model, human_bytes
from src.exporters import format_clock, to_srt, to_txt, to_vtt
from src.transcriber import Transcription, detect_device, load_model, transcribe
from ui import components as ui

LOGO = Path(__file__).parent / "assets" / "logo.png"
st.set_page_config(page_title="Transcriptor", page_icon=str(LOGO), layout="centered")
ui.inject_css()


@st.cache_resource(show_spinner=False)
def get_model(model_path: str):
    """El modelo se carga una sola vez y se reutiliza entre transcripciones."""
    return load_model(model_path)


def ensure_model(model_size: str) -> str:
    """Devuelve la ruta local del modelo; si no está, lo descarga mostrando el avance."""
    path = cached_model_path(model_size)
    if path:
        return path

    title = f"Modelo «{model_size}»"
    card = st.empty()
    card.html(ui.job_card(title, "Preparando descarga…", 0))

    def show(p: DownloadProgress):
        speed = f" · {human_bytes(p.speed)}/s" if p.speed else ""
        if p.total:
            status = f"{human_bytes(p.downloaded)} / {human_bytes(p.total)}{speed}"
        else:
            status = f"{human_bytes(p.downloaded)}{speed}"
        card.html(ui.job_card(title, status, p.fraction))

    try:
        path = download_model(model_size, on_progress=show)
    except Exception as e:
        card.html(ui.job_card(title, "No se pudo descargar", 0, error=True))
        st.error(f"No se pudo descargar el modelo: {e}")
        st.stop()

    card.html(ui.job_card(title, "✓ descargado · solo se descarga una vez", 1))
    return path


# ---------- Barra lateral ----------
with st.sidebar:
    ui.sidebar_brand(LOGO)
    model_size = st.selectbox(
        ":material/auto_awesome: Modelo",
        options=list(MODEL_SIZES),
        index=list(MODEL_SIZES).index(DEFAULT_MODEL),
        format_func=lambda k: MODEL_SIZES[k],
        help="La primera vez se descarga el modelo elegido: "
        + ", ".join(f"{k} {v}" for k, v in MODEL_DOWNLOAD.items()),
    )
    language = st.selectbox(
        ":material/language: Idioma",
        options=list(LANGUAGES),
        index=list(LANGUAGES).index(DEFAULT_LANGUAGE),
        format_func=lambda k: LANGUAGES[k],
    )
    with st.container(key="options"):
        vad = st.toggle("Saltar silencios", value=True)
        ui.sidebar_hint("Más rápido y sin texto inventado")
        timestamps_in_txt = st.toggle("Tiempos en el .txt", value=False)

    device, compute = detect_device()
    ui.device_badge(device, compute, __version__)

# ---------- Contenido principal ----------
ui.hero()

files = st.file_uploader(
    "Sube uno o varios audios",
    type=AUDIO_EXTENSIONS,
    accept_multiple_files=True,
    label_visibility="collapsed",
)

run = False
if files:
    label = f"Transcribir {len(files)} audios" if len(files) > 1 else "Transcribir audio"
    run = st.button(label, type="primary", use_container_width=True, key="run")

if run:
    model_path = ensure_model(model_size)
    with st.spinner(f"Cargando modelo «{model_size}» en {device.upper()}…"):
        model = get_model(model_path)

    cards = {f.name: st.empty() for f in files}
    for f in files:
        cards[f.name].html(ui.job_card(f.name, f"En cola · {f.size / 1e6:.1f} MB", 0))

    results: dict[str, Transcription] = {}
    for f in files:
        card = cards[f.name]
        card.html(ui.job_card(f.name, "Analizando…", 0))
        suffix = Path(f.name).suffix or ".audio"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(f.getbuffer())
            tmp_path = Path(tmp.name)

        def on_progress(p: float, name=f.name, card=card):
            card.html(ui.job_card(name, f"Transcribiendo… {p:.0%}", p))

        try:
            t = transcribe(model, tmp_path, language=language, vad_filter=vad, on_progress=on_progress)
            results[f.name] = t
            card.html(ui.job_card(f.name, f"✓ {format_clock(t.duration)} de audio", 1))
        except Exception as e:  # audio corrupto, formato raro, etc.
            card.html(ui.job_card(f.name, "Error al transcribir", 0, error=True))
            st.error(f"No se pudo transcribir **{f.name}**: {e}")
        finally:
            tmp_path.unlink(missing_ok=True)

    st.session_state["results"] = results

elif st.session_state.get("results"):
    # Tras cualquier recarga, las tarjetas de los audios ya transcritos se mantienen
    for name, t in st.session_state["results"].items():
        st.html(ui.job_card(name, f"✓ {format_clock(t.duration)} de audio", 1))

# Los resultados se guardan en session_state para que no se pierdan
# al pulsar un botón de descarga (Streamlit vuelve a ejecutar el script).
for i, (name, t) in enumerate(st.session_state.get("results", {}).items()):
    lang = LANGUAGES.get(t.language, t.language)
    with st.container(key=f"result_{i}"):
        head, toggle = st.columns([3, 2], vertical_alignment="center")
        with head:
            ui.result_header(name, format_clock(t.duration), f"{lang} · {t.language_probability:.0%}")
        with toggle:
            view = st.segmented_control(
                "Vista",
                ["Texto", "Con tiempos"],
                default="Texto",
                key=f"view_{i}",
                label_visibility="collapsed",
            )

        if view == "Con tiempos":
            ui.transcript_segments([(format_clock(s.start), s.text.strip()) for s in t.segments])
        else:
            ui.transcript(t.text)

        stem = Path(name).stem
        with st.container(key=f"actions_{i}", horizontal=True, vertical_alignment="center"):
            ui.copy_button(t.text, key=f"copy_{i}")
            st.space("stretch")
            ui.download_label()
            for ext, data in (
                ("txt", to_txt(t, timestamps_in_txt)),
                ("srt", to_srt(t.segments)),
                ("vtt", to_vtt(t.segments)),
            ):
                st.download_button(
                    f".{ext}", data, f"{stem}.{ext}", icon=":material/download:", key=f"{ext}_{i}"
                )
