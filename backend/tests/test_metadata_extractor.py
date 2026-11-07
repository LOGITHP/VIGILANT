import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.models.video import Video, MetadataStatus, ValidationStatus
from app.services.metadata_extractor import MetadataInspectionService


@pytest.mark.asyncio
async def test_inspect_video_pipeline(db_session):
    video_id = uuid.uuid4()
    video = Video(
        id=video_id,
        title="CAM-01 Gate Inspection Test",
        original_filename="gate_feed.mp4",
        file_size=204800,
        content_type="video/mp4",
        s3_key=f"videos/{video_id}/gate_feed.mp4",
        sha256_checksum="abc1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcd",
        metadata_status=MetadataStatus.PENDING,
        validation_status=ValidationStatus.PENDING
    )
    db_session.add(video)
    await db_session.commit()

    sample_ffprobe_data = {
        "format": {
            "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
            "format_long_name": "QuickTime / MOV",
            "duration": "14.500000",
            "bit_rate": "1500000",
            "start_time": "0.000000",
            "size": "204800"
        },
        "streams": [
            {
                "index": 0,
                "codec_type": "video",
                "codec_name": "h264",
                "codec_long_name": "H.264 / AVC",
                "width": 1920,
                "height": 1080,
                "r_frame_rate": "30000/1001",
                "pix_fmt": "yuv420p",
                "time_base": "1/90000",
                "start_time": "0.000000",
                "duration": "14.500000",
                "nb_frames": "435",
                "disposition": {"default": 1, "attached_pic": 0}
            },
            {
                "index": 1,
                "codec_type": "audio",
                "codec_name": "aac",
                "sample_rate": "48000",
                "channels": 2,
                "channel_layout": "stereo",
                "duration": "14.500000",
                "disposition": {"default": 1}
            }
        ]
    }

    with patch("app.services.metadata_extractor.get_minio_client") as mock_get_minio, \
         patch.object(MetadataInspectionService, "run_ffprobe", new_callable=AsyncMock) as mock_probe, \
         patch("os.path.getsize", return_value=204800):

        mock_minio = MagicMock()
        mock_get_minio.return_value = mock_minio
        mock_probe.return_value = sample_ffprobe_data

        inspection = await MetadataInspectionService.inspect_video(video_id, db_session=db_session)

        assert inspection is not None
        assert inspection.metadata_status == MetadataStatus.COMPLETED
        assert inspection.validation_status == ValidationStatus.PENDING
        assert inspection.width == 1920
        assert inspection.height == 1080
        assert inspection.fps == 29.97
        assert inspection.rational_fps == "30000/1001"
        assert inspection.video_codec == "h264"
        assert inspection.has_audio is True
        assert inspection.audio_codec == "aac"
        assert len(inspection.streams) == 2


@pytest.mark.asyncio
async def test_inspect_video_error_handling(db_session):
    video_id = uuid.uuid4()
    video = Video(
        id=video_id,
        title="Corrupted Footage Test",
        original_filename="corrupted.mp4",
        file_size=1024,
        content_type="video/mp4",
        s3_key=f"videos/{video_id}/corrupted.mp4",
        metadata_status=MetadataStatus.PENDING,
        validation_status=ValidationStatus.PENDING
    )
    db_session.add(video)
    await db_session.commit()

    with patch("app.services.metadata_extractor.get_minio_client") as mock_get_minio, \
         patch.object(MetadataInspectionService, "run_ffprobe", new_callable=AsyncMock) as mock_probe, \
         patch("os.path.getsize", return_value=1024):

        mock_minio = MagicMock()
        mock_get_minio.return_value = mock_minio
        mock_probe.side_effect = RuntimeError("Invalid data found when processing input")

        inspection = await MetadataInspectionService.inspect_video(video_id, db_session=db_session)

        assert inspection is not None
        assert inspection.metadata_status == MetadataStatus.FAILED
        assert inspection.validation_status == ValidationStatus.PENDING
        assert "Invalid data found" in (inspection.error_message or "")
