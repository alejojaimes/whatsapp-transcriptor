"""Piezas visuales en HTML para la app de Streamlit."""

from __future__ import annotations

import base64
import json
from functools import lru_cache
from html import escape
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

HERE = Path(__file__).parent

# Íconos de Lucide (los mismos del diseño), en SVG en línea.
_ICON = {
    "lock": '<rect width="18" height="11" x="3" y="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "cpu": '<rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/>'
    '<path d="M15 2v2M15 20v2M2 15h2M2 9h2M20 15h2M20 9h2M9 2v2M9 20v2"/>',
    "file-audio": '<path d="M17.5 22h.5a2 2 0 0 0 2-2V7l-5-5H6a2 2 0 0 0-2 2v3"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/>'
    '<path d="M2 19a2 2 0 1 1 4 0v1a2 2 0 1 1-4 0v-4a6 6 0 0 1 12 0v4a2 2 0 1 1-4 0v-1a2 2 0 1 1 4 0"/>',
    "sparkles": '<path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5'
    'l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063'
    'a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/>',
}


def icon(name: str, size: int = 16, color: str = "currentColor") -> str:
    """Ícono como <img>: st.html limpia las etiquetas <svg> en línea, pero no las imágenes."""
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round">{_ICON[name]}</svg>'
    )
    uri = "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
    return f'<img class="tx-ico" src="{uri}" width="{size}" height="{size}" alt="">'

WHITE, MUTED, SECONDARY_FG = "#FFFFFF", "#636780", "#2C2986"


@lru_cache
def _css() -> str:
    return (HERE / "theme.css").read_text(encoding="utf-8")


@lru_cache
def _data_uri(path: str) -> str:
    return "data:image/png;base64," + base64.b64encode(Path(path).read_bytes()).decode()


def inject_css() -> None:
    # Ojo: el CSS no puede contener "<" (ni en comentarios). El limpiador de HTML
    # de Streamlit descarta el bloque <style> completo si lo encuentra.
    st.html(f"<style>{_css()}</style>")


# ---------- Barra lateral ----------
def sidebar_brand(logo: Path) -> None:
    st.html(f'<div class="tx-brand"><img src="{_data_uri(str(logo))}" alt=""><span>Transcriptor</span></div>')


def sidebar_hint(text: str) -> None:
    st.html(f'<div class="tx-hint">{escape(text)}</div>')


def device_badge(device: str, compute: str, version: str) -> None:
    st.html(
        f'<div class="tx-device">{icon("cpu", 14, MUTED)} {escape(device.upper())} ({escape(compute)}) · v{escape(version)}</div>'
    )


# ---------- Hero ----------
def hero() -> None:
    bars = "".join(f'<span style="height:{h}%"></span>' for h in (40, 70, 100, 60, 85, 45))
    st.html(
        f"""
        <section class="tx-hero">
          <div class="tx-hero__waves">{bars}</div>
          <span class="tx-pill">{icon("lock", 12, WHITE)} Privado · funciona sin internet</span>
          <h1>Convierte tus audios a texto en segundos</h1>
          <p>Notas de voz de WhatsApp (.opus, .ogg), MP3, M4A, WAV y más. Gratis, en tu propia computadora.</p>
        </section>
        """
    )


# ---------- Tarjetas de progreso ----------
def job_card(name: str, status: str, progress: float, error: bool = False) -> str:
    """HTML de una tarjeta. Se pinta con placeholder.html(...) para poder actualizarla."""
    pct = max(0.0, min(progress, 1.0)) * 100
    cls = "tx-job tx-job--error" if error else "tx-job"
    return f"""
    <div class="{cls}">
      <div class="tx-job__icon">{icon("file-audio", 20, SECONDARY_FG)}</div>
      <div class="tx-job__body">
        <div class="tx-job__top">
          <span class="tx-job__name">{escape(name)}</span>
          <span class="tx-job__status">{escape(status)}</span>
        </div>
        <div class="tx-job__track"><div class="tx-job__bar" style="width:{pct:.1f}%"></div></div>
      </div>
    </div>
    """


# ---------- Resultado ----------
def result_header(name: str, duration: str, language: str) -> None:
    st.html(
        f"""
        <h2 class="tx-result__name">{escape(name)}</h2>
        <div class="tx-tags"><span class="tx-tag">⏱ {escape(duration)}</span><span class="tx-tag">{escape(language)}</span></div>
        """
    )


def transcript(text: str) -> None:
    st.html(f'<div class="tx-transcript"><p>{escape(text)}</p></div>')


def transcript_segments(rows: list[tuple[str, str]]) -> None:
    items = "".join(
        f'<div class="tx-seg"><span class="tx-seg__time">{escape(t)}</span><span>{escape(s)}</span></div>'
        for t, s in rows
    )
    st.html(f'<div class="tx-transcript">{items}</div>')


def download_label() -> None:
    st.html('<div class="tx-dl-label">Descargar</div>')


def copy_button(text: str, key: str) -> None:
    """Botón 'Copiar texto'. Streamlit no trae uno, así que va en un iframe con un poco de JS."""
    payload = json.dumps(text)
    components.html(
        f"""
        <style>
          body {{ margin: 0; font-family: "Plus Jakarta Sans", system-ui, sans-serif; }}
          button {{ all: unset; cursor: pointer; display: inline-flex; align-items: center; gap: 8px;
                   padding: 8px 12px; border-radius: 12px; font-size: 14px; font-weight: 500; color: #181844; }}
          button:hover {{ background: #EFF1FA; }}
          svg {{ width: 16px; height: 16px; }}
        </style>
        <button id="b" data-key="{escape(key)}">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect width="14" height="14" x="8" y="8" rx="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>
          <span>Copiar texto</span>
        </button>
        <script>
          const text = {payload};
          const b = document.getElementById("b"), label = b.querySelector("span");
          b.onclick = async () => {{
            try {{ await navigator.clipboard.writeText(text); }}
            catch (e) {{
              const t = document.createElement("textarea"); t.value = text; document.body.appendChild(t);
              t.select(); document.execCommand("copy"); t.remove();
            }}
            label.textContent = "Copiado ✓";
            setTimeout(() => label.textContent = "Copiar texto", 1500);
          }};
        </script>
        """,
        height=40,
    )
