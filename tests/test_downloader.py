import time

from src import downloader
from src.downloader import DownloadProgress, download_model, human_bytes, repo_id_for


def test_repo_id_for():
    assert repo_id_for("small") == "Systran/faster-whisper-small"
    assert repo_id_for("usuario/mi-modelo") == "usuario/mi-modelo"


def test_human_bytes():
    assert human_bytes(500) == "500 B"
    assert human_bytes(480 * 1024**2) == "480.0 MB"
    assert human_bytes(3 * 1024**3) == "3.0 GB"


def test_download_reports_progress(tmp_path, monkeypatch):
    """Simula una descarga que escribe el archivo poco a poco."""
    total = 4 * 1024
    monkeypatch.setattr(downloader, "repo_cache_dir", lambda _: tmp_path)
    monkeypatch.setattr(downloader, "remote_size", lambda _: total)

    def fake_download(repo_id):
        with open(tmp_path / "model.bin.incomplete", "wb") as fh:
            for _ in range(4):
                fh.write(b"x" * 1024)
                fh.flush()
                time.sleep(0.05)
        return str(tmp_path)

    seen: list[DownloadProgress] = []
    path = download_model("small", on_progress=seen.append, poll_interval=0.02, _download=fake_download)

    assert path == str(tmp_path)
    fractions = [p.fraction for p in seen]
    assert fractions == sorted(fractions)  # nunca retrocede
    assert any(0 < f < 1 for f in fractions)  # hubo pasos intermedios
    assert seen[-1].fraction == 1.0


def test_download_error_is_raised(tmp_path, monkeypatch):
    monkeypatch.setattr(downloader, "repo_cache_dir", lambda _: tmp_path)
    monkeypatch.setattr(downloader, "remote_size", lambda _: 0)

    def boom(repo_id):
        raise RuntimeError("sin conexión")

    try:
        download_model("small", _download=boom, poll_interval=0.01)
    except RuntimeError as e:
        assert "sin conexión" in str(e)
    else:
        raise AssertionError("debió lanzar el error")
