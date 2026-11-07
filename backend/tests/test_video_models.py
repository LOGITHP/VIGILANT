import uuid
from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.models.video import Video, VideoUploadSession, VideoChunk, VideoStatus


@pytest.mark.asyncio
async def test_video_models_crud(db_session: AsyncSession):
    # 1. Create a user
    user = User(
        id=uuid.uuid4(),
        email="operator_video@vigilant.ai",
        hashed_password="mock_hashed_password",
        full_name="Video Test Operator",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()

    # 2. Create Video
    video = Video(
        id=uuid.uuid4(),
        title="Gate 1 Surveillance",
        description="Entryway capture",
        original_filename="gate1_capture.mp4",
        file_size=10485760,
        content_type="video/mp4",
        s3_key=f"videos/{uuid.uuid4()}/gate1_capture.mp4",
        status=VideoStatus.UPLOADING,
        uploaded_by_id=user.id
    )
    db_session.add(video)
    await db_session.commit()

    # 3. Create Upload Session
    session = VideoUploadSession(
        id=uuid.uuid4(),
        video_id=video.id,
        total_chunks=2,
        chunk_size=5242880,
        temp_directory="/tmp/vigilant_uploads/mock_session",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
    )
    db_session.add(session)
    await db_session.commit()

    # 4. Create Video Chunk
    chunk = VideoChunk(
        id=uuid.uuid4(),
        upload_session_id=session.id,
        chunk_index=0,
        chunk_size=5242880,
        sha256_checksum="a" * 64
    )
    db_session.add(chunk)
    await db_session.commit()

    # Query back and verify relationships
    stmt = select(Video).where(Video.id == video.id)
    res = await db_session.execute(stmt)
    saved_video = res.scalar_one()

    assert saved_video.title == "Gate 1 Surveillance"
    assert saved_video.status == VideoStatus.UPLOADING
    assert saved_video.uploader.email == "operator_video@vigilant.ai"
    assert len(saved_video.upload_sessions) == 1
    assert len(saved_video.upload_sessions[0].chunks) == 1
    assert saved_video.upload_sessions[0].chunks[0].chunk_index == 0
