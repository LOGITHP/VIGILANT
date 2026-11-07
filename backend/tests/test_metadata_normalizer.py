import pytest
from app.services.metadata_normalizer import MetadataNormalizer


def test_parse_rational_number():
    norm = MetadataNormalizer

    # NTSC standard 29.97 fps
    fps, rat = norm.parse_rational_number("30000/1001")
    assert fps == 29.97
    assert rat == "30000/1001"

    # PAL 25 fps
    fps, rat = norm.parse_rational_number("25/1")
    assert fps == 25.0
    assert rat == "25/1"

    # 23.976 cinematic
    fps, rat = norm.parse_rational_number("24000/1001")
    assert fps == 23.976
    assert rat == "24000/1001"

    # Edge cases
    assert norm.parse_rational_number("0/0") == (None, None)
    assert norm.parse_rational_number("0/1") == (None, None)
    assert norm.parse_rational_number("N/A") == (None, None)
    assert norm.parse_rational_number("") == (None, None)
    assert norm.parse_rational_number(None) == (None, None)
    assert norm.parse_rational_number("invalid_string") == (None, None)


def test_select_primary_video_stream_with_attached_picture():
    # Simulation: Stream 0 is an attached picture (poster art)
    # Stream 1 is the actual continuous H.264 video stream
    streams = [
        {
            "index": 0,
            "codec_type": "video",
            "codec_name": "mjpeg",
            "width": 1280,
            "height": 720,
            "disposition": {"attached_pic": 1, "default": 0}
        },
        {
            "index": 1,
            "codec_type": "video",
            "codec_name": "h264",
            "width": 1920,
            "height": 1080,
            "disposition": {"attached_pic": 0, "default": 1}
        },
        {
            "index": 2,
            "codec_type": "audio",
            "codec_name": "aac"
        }
    ]

    selected = MetadataNormalizer.select_primary_video_stream(streams)
    assert selected is not None
    assert selected["index"] == 1
    assert selected["codec_name"] == "h264"
    assert selected["width"] == 1920


def test_select_primary_video_stream_resolution_tiebreaker():
    # Stream 0: 720p thermal stream
    # Stream 1: 4K optical stream
    streams = [
        {
            "index": 0,
            "codec_type": "video",
            "codec_name": "h264",
            "width": 1280,
            "height": 720,
            "disposition": {"default": 0}
        },
        {
            "index": 1,
            "codec_type": "video",
            "codec_name": "hevc",
            "width": 3840,
            "height": 2160,
            "disposition": {"default": 0}
        }
    ]

    selected = MetadataNormalizer.select_primary_video_stream(streams)
    assert selected is not None
    assert selected["index"] == 1
    assert selected["codec_name"] == "hevc"
    assert selected["width"] == 3840


def test_select_primary_audio_stream():
    # Test audio stream detection
    streams = [
        {"index": 0, "codec_type": "video", "codec_name": "h264"},
        {"index": 1, "codec_type": "audio", "codec_name": "aac", "sample_rate": "48000"}
    ]
    audio = MetadataNormalizer.select_primary_audio_stream(streams)
    assert audio is not None
    assert audio["index"] == 1
    assert audio["codec_name"] == "aac"

    # Test silent video feed (no audio)
    silent_streams = [
        {"index": 0, "codec_type": "video", "codec_name": "h264"}
    ]
    assert MetadataNormalizer.select_primary_audio_stream(silent_streams) is None
