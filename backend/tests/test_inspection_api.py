import uuid
import pytest
from httpx import AsyncClient

from app.models.video import Video, VideoInspection, VideoStream, MetadataStatus, ValidationStatus


@pytest.mark.asyncio
async def test_video_inspection_api(client: AsyncClient, db_session):
    # 1. Login
    await client.post("/api/v1/auth/register", json={
        "email": "inspector@vigilant.ai",
        "password": "Password123!",
        "full_name": "Media Analyst"
    })
    login_res = await client.post("/api/v1/auth/login", json={
        "username": "inspector@vigilant.ai",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Seed video
    video_id = uuid.uuid4()
    video = Video(
        id=video_id,
        title="CAM-02 Corridor Footage",
        original_filename="corridor.mp4",
        file_size=5000000,
        content_type="video/mp4",
        s3_key=f"videos/{video_id}/corridor.mp4",
        metadata_status=MetadataStatus.PENDING,
        validation_status=ValidationStatus.PENDING
    )
    db_session.add(video)
    await db_session.commit()

    # 3. Query inspection before completion -> 404
    pre_res = await client.get(f"/api/v1/videos/{video_id}/inspection", headers=headers)
    assert pre_res.status_code == 404

    # 4. Seed inspection report
    insp_id = uuid.uuid4()
    inspection = VideoInspection(
        id=insp_id,
        video_id=video_id,
        extractor_version="1.0.0",
        metadata_status=MetadataStatus.COMPLETED,
        validation_status=ValidationStatus.PENDING,
        file_size=5000000,
        file_format="mov,mp4,m4a,3gp,3g2,mj2",
        format_name="mp4",
        duration_seconds=30.0,
        bitrate=1200000,
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
        inspection_id=insp_id,
        stream_index=0,
        stream_type="video",
        codec_name="h264",
        is_primary=True,
        is_default=True,
        width=1920,
        height=1080
    )
    db_session.add(stream0)
    await db_session.commit()
    db_session.expire_all()

    # 5. Query inspection report
    get_res = await client.get(f"/api/v1/videos/{video_id}/inspection", headers=headers)
    assert get_res.status_code == 200
    data = get_res.json()

    assert data["inspection_id"] == str(insp_id)
    assert data["video_id"] == str(video_id)
    assert data["metadata_status"] == "COMPLETED"
    assert data["validation_status"] == "PENDING"
    assert data["file_info"]["original_filename"] == "corridor.mp4"
    assert data["container_info"]["duration_seconds"] == 30.0
    assert data["video_stream"]["width"] == 1920
    assert data["audio_stream"]["codec_name"] == "aac"
    assert len(data["all_streams"]) == 1

    # 6. Trigger on-demand re-inspection
    post_res = await client.post(f"/api/v1/videos/{video_id}/inspect", headers=headers)
    assert post_res.status_code == 202
    assert post_res.json()["status"] == "EXTRACTING"
