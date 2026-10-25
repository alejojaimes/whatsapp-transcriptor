<div align="center">


<h1><img src="assets/logo.svg" alt="" width="44" align="center"> Transcriptor</h1>

**Tus audios a texto, gratis y sin salir de tu computadora.**

[![Python](https://img.shields.io/badge/python-3.9+-4F46E5?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![Streamlit](https://img.shields.io/badge/streamlit-app-4F46E5?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![faster-whisper](https://img.shields.io/badge/faster--whisper-STT-4F46E5?style=flat-square)](https://github.com/SYSTRAN/faster-whisper)
[![License: MIT](https://img.shields.io/badge/license-MIT-4F46E5?style=flat-square)](./LICENSE)

</div>

---

Una app web local que convierte audio en texto con [faster-whisper](https://github.com/SYSTRAN/faster-whisper), la versión optimizada de Whisper, el modelo de reconocimiento de voz de código abierto de OpenAI. La interfaz está hecha en [Streamlit](https://streamlit.io): arrastras el audio, pulsas un botón y te llevas el texto.

Todo corre en tu máquina. No hay API de pago ni cuentas de por medio, y ningún audio sale de tu computadora. Solo necesitas internet la primera vez, para descargar el modelo.

Nació de una necesidad concreta: transcribir notas de voz de WhatsApp sin tener que convertirlas a MP3 ni subirlas a un servicio externo.

---

## Qué hace

| Función | Detalle |
|---------|---------|
| Formatos | Notas de voz de WhatsApp (`.opus`, `.ogg`) sin convertir, además de MP3, M4A, WAV, FLAC, WEBM y MP4 |
| Varios archivos | Sube un lote de audios y transcribe todos de una vez |
| Idioma | Detección automática o idioma fijo (español, inglés, portugués, francés, italiano, alemán) |
| Modelos | De `tiny` a `large-v3`, según prefieras velocidad o precisión |
| Hardware | Usa GPU NVIDIA si la hay; si no, CPU con cuantización `int8` |
| Silencios | Filtro VAD que salta las partes sin voz y evita texto inventado |
| Exportación | `.txt` (con o sin tiempos), `.srt` y `.vtt` para subtítulos |

> No hace falta instalar FFmpeg. faster-whisper decodifica el audio con PyAV, que ya lo trae incluido.

---

## Cómo empezar

```bash
git clone https://github.com/alejojaimes/transcriptor.git
cd transcriptor

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

La app se abre en `http://localhost:8501`. Sube tus audios, elige el modelo y el idioma en la barra lateral y pulsa **Transcribir**.

Necesitas Python 3.9 o superior y unos 2 GB de RAM libres para el modelo `small`.

### ¿Qué modelo elegir?

| Modelo | Tamaño | Cuándo usarlo |
|--------|--------|---------------|
| `tiny` | ~75 MB | Pruebas rápidas |
| `base` | ~145 MB | Audios claros en un PC modesto |
| `small` | ~480 MB | **El mejor equilibrio en CPU** |
| `medium` | ~1.5 GB | Más precisión, lento sin GPU |
| `large-v3` | ~3 GB | Máxima precisión, ideal con GPU |

Los modelos quedan guardados en la caché de Hugging Face (`~/.cache/huggingface`), así que cada uno se descarga una sola vez.

---

## Estructura

```
transcriptor/
├── app.py                   ← interfaz en Streamlit
├── transcriptor/
│   ├── config.py            ← modelos, idiomas y formatos soportados
│   ├── transcriber.py       ← carga del modelo y transcripción
│   └── exporters.py         ← exportación a txt, srt y vtt
├── tests/                   ← pruebas con un modelo simulado (no descargan nada)
├── .streamlit/config.toml   ← límite de subida y tema
├── requirements.txt
└── requirements-dev.txt
```

La lógica de `transcriptor/` no depende de Streamlit. Si mañana quieres una CLI, una API o un bot, la reutilizas tal cual y solo cambias la interfaz.

Para correr los tests:

```bash
pip install -r requirements-dev.txt
pytest
```

---

## Lo que viene

- [ ] Grabar directamente desde el micrófono
- [ ] Diarización, para saber quién dice qué
- [ ] Traducción al inglés con `task="translate"`
- [ ] Versión de línea de comandos para procesar carpetas completas

---

## Sobre el autor

Soy un ingeniero que enseña. El contexto, la teoría y el paso a paso de mis proyectos los publico en [ajteaches.dev](https://www.ajteaches.dev).

---

## Licencia

Distribuido bajo la [licencia MIT](./LICENSE). Puedes usar, modificar y compartir el código libremente dando el crédito correspondiente.
