from src.exporters import format_clock, to_srt, to_txt, to_vtt
from src.transcriber import Segment, Transcription

SEGS = [
    Segment(0.0, 2.5, " Hola, ¿cómo estás?"),
    Segment(2.5, 3661.042, " Todo bien."),
]
T = Transcription(language="es", language_probability=0.99, duration=3662, segments=SEGS)


def test_text_joins_segments():
    assert T.text == "Hola, ¿cómo estás? Todo bien."


def test_txt_with_timestamps():
    assert to_txt(T, with_timestamps=True) == "[0:00] Hola, ¿cómo estás?\n[0:02] Todo bien.\n"


def test_srt_format():
    srt = to_srt(SEGS)
    assert srt.startswith("1\n00:00:00,000 --> 00:00:02,500\nHola, ¿cómo estás?\n")
    assert "2\n00:00:02,500 --> 01:01:01,042\nTodo bien.\n" in srt


def test_vtt_format():
    vtt = to_vtt(SEGS)
    assert vtt.startswith("WEBVTT\n")
    assert "00:00:00.000 --> 00:00:02.500" in vtt


def test_format_clock():
    assert format_clock(65) == "1:05"
    assert format_clock(3725) == "1:02:05"
