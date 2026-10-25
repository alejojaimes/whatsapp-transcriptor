from types import SimpleNamespace

from src.transcriber import transcribe


class FakeModel:
    """Imita la interfaz de faster_whisper.WhisperModel sin descargar nada."""

    def __init__(self):
        self.kwargs = None

    def transcribe(self, path, **kwargs):
        self.kwargs = kwargs
        segs = [
            SimpleNamespace(start=0.0, end=5.0, text=" Primera parte."),
            SimpleNamespace(start=5.0, end=10.0, text=" Segunda parte."),
        ]
        info = SimpleNamespace(language="es", language_probability=0.97, duration=10.0)
        return iter(segs), info


def test_transcribe_collects_segments_and_progress():
    progress = []
    model = FakeModel()
    t = transcribe(model, "audio.opus", language="es", on_progress=progress.append)

    assert t.text == "Primera parte. Segunda parte."
    assert t.language == "es"
    assert progress == [0.5, 1.0, 1.0]
    assert model.kwargs["language"] == "es"


def test_auto_language_passes_none():
    model = FakeModel()
    transcribe(model, "audio.opus", language="auto")
    assert model.kwargs["language"] is None
