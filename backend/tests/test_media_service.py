import json
from unittest.mock import MagicMock, patch
import pytest
from app.services.media_service import MediaProcessingService


def test_extract_metadata_success():
    sample_ffprobe_output = {
        "format": {
            "duration": "125.50",
            "bit_rate": "4500000"
        },
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1920,
                "height": 1080,
                "r_frame_rate": "30/1"
            },
            {
                "codec_type": "audio",
                "codec_name": "aac"
            }
        ]
    }

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout=json.dumps(sample_ffprobe_output),
            stderr=""
        )

        meta = MediaProcessingService.extract_metadata("/tmp/mock_video.mp4")

        assert meta["duration_seconds"] == 125.50
        assert meta["width"] == 1920
        assert meta["height"] == 1080
        assert meta["fps"] == 30.0
        assert meta["video_codec"] == "h264"
        assert meta["audio_codec"] == "aac"
        assert meta["bitrate"] == 4500000


def test_extract_metadata_failure_fallback():
    with patch("subprocess.run", side_effect=FileNotFoundError("ffprobe not found")):
        meta = MediaProcessingService.extract_metadata("/tmp/mock_video.mp4")
        assert meta["duration_seconds"] is None
        assert meta["width"] is None
        assert meta["fps"] is None


def test_generate_thumbnail_success():
    fake_jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 100

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout=fake_jpeg,
            stderr=""
        )

        thumb = MediaProcessingService.generate_thumbnail("/tmp/mock_video.mp4", timestamp_sec=1.5)
        assert thumb == fake_jpeg
        assert thumb.startswith(b"\xff\xd8\xff")
