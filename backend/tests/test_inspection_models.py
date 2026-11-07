import uuid
import pytest
from sqlalchemy import select
from app.models.video import Video, VideoInspection, VideoStream, MetadataStatus, ValidationStatus


@pytest.mark.asyncio
async def test_inspection_models_lifecycle(db_session):
    video_id = uuid.uuid4()
    video = Video(
        id=video_id,
        title="CAM-05 Perimeter Inspection Test",
        original_filename="perimeter_cam05.mp4",
        file_size=1048576,
        content_type="video/mp4",
        s3_key=f"videos/{video_id}/perimeter_cam05.mp4",
        metadata_status=MetadataStatus.EXTRACTING,
        validation_status=ValidationStatus.PENDING
    )
    db_session.add(video)
    await db_session.commit()

    inspection_id = uuid.uuid4()
    inspection = VideoInspection(
        id=inspection_id,
        video_id=video_id,
        extractor_version="1.0.0",
        metadata_status=MetadataStatus.COMPLETED,
        validation_status=ValidationStatus.PENDING,
        file_size=1048576,
        file_format="mov,mp4,m4a,3gp,3g2,mj2",
        format_name="mp4",
        duration_seconds=12.5,
        bitrate=650000,
        primary_video_stream_index=0,
        video_codec="h264",
        width=1920,
        height=1080,
        fps=30.0,
        rational_fps="30/1",
        pixel_format="yuv420p",
        time_base="1/90000",
        has_audio=True,
        primary_audio_stream_index=1,
        audio_codec="aac",
        audio_sample_rate=48000,
        audio_channels=2,
        audio_channel_layout="stereo"
    )
    db_session.add(inspection)
    await db_session.commit()

    stream0 = VideoStream(
        inspection_id=inspection_id,
        stream_index=0,
        stream_type="video",
        codec_name="h264",
        is_primary=True,
        is_default=True,
        width=1920,
        height=1080,
        fps=30.0,
        time_base="1/90000"
    )
    stream1 = VideoStream(
        inspection_id=inspection_id,
        stream_index=1,
        stream_type="audio",
        codec_name="aac",
        is_primary=True,
        sample_rate=48000,
        channels=2
    )
    db_session.add_all([stream0, stream1])
    await db_session.commit()

    # Query back
    stmt = select(Video).where(Video.id == video_id)
    res = await db_session.execute(stmt)
    saved_video = res.scalar_one()

    assert len(saved_video.inspections) == 1
    insp = saved_video.inspections[0]
    assert insp.video_codec == "h264"
    assert insp.width == 1920
    assert insp.has_audio is True
    assert len(insp.streams) == 2
    assert insp.streams[0].stream_type == "video"
    assert insp.streams[1].stream_type == "audio"
