import uuid
from datetime import datetime, timezone
from app.schemas.inspection import (
    FileInfoSchema,
    ContainerInfoSchema,
    VideoStreamInfoSchema,
    AudioStreamInfoSchema,
    StreamSummarySchema,
    VideoInspectionReportResponse
)


def test_inspection_schemas_serialization():
    file_info = FileInfoSchema(
        original_filename="camera_01_recording.mp4",
        file_size=52428800,
        file_format="mov,mp4,m4a,3gp,3g2,mj2",
        sha256_checksum="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        upload_timestamp=datetime.now(timezone.utc)
    )

    container_info = ContainerInfoSchema(
        format_name="mp4",
        format_long_name="QuickTime / MOV",
        duration_seconds=932.45,
        bitrate=4500000,
        start_time=0.0,
        container_size=52428800
    )

    video_stream = VideoStreamInfoSchema(
        stream_index=0,
        codec_name="h264",
        codec_long_name="H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10",
        width=1920,
        height=1080,
        fps=30.0,
        rational_fps="30/1",
        pixel_format="yuv420p",
        time_base="1/90000",
        start_timestamp=0.0,
        duration_seconds=932.45,
        reported_frame_count=27973
    )

    audio_stream = AudioStreamInfoSchema(
        has_audio=True,
        stream_index=1,
        codec_name="aac",
        sample_rate=48000,
        channels=2,
        channel_layout="stereo",
        duration_seconds=932.40
    )

    streams = [
        StreamSummarySchema(
            stream_index=0,
            stream_type="video",
            codec_name="h264",
            is_primary=True,
            is_default=True,
            width=1920,
            height=1080
        ),
        StreamSummarySchema(
            stream_index=1,
            stream_type="audio",
            codec_name="aac",
            is_primary=True,
            sample_rate=48000
        )
    ]

    report = VideoInspectionReportResponse(
        inspection_id=uuid.uuid4(),
        video_id=uuid.uuid4(),
        extractor_version="1.0.0",
        metadata_status="COMPLETED",
        validation_status="PENDING",
        inspected_at=datetime.now(timezone.utc),
        file_info=file_info,
        container_info=container_info,
        video_stream=video_stream,
        audio_stream=audio_stream,
        all_streams=streams
    )

    data = report.model_dump()
    assert data["file_info"]["original_filename"] == "camera_01_recording.mp4"
    assert data["video_stream"]["width"] == 1920
    assert data["audio_stream"]["has_audio"] is True
    assert len(data["all_streams"]) == 2
