import os
import re
import uuid
import asyncio
from typing import Optional, List
from datetime import datetime, timezone, timedelta

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    Query,
    Request,
    Response,
    status,
    BackgroundTasks
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.video import (
    Video,
    VideoUploadSession,
    VideoChunk,
    VideoStatus,
    VideoSourceType,
    VideoInspection,
    VideoStream
)
from app.services.storage_service import StorageService
from app.services.media_service import MediaProcessingService
from app.services.metadata_extractor import MetadataInspectionService
from app.schemas.video import (
    VideoUploadInitRequest,
    VideoUploadInitResponse,
    ChunkUploadResponse,
    UploadStatusResponse,
    UploadCompleteRequest,
    LiveCaptureRequest,
    VideoResponse,
    VideoListResponse
)
from app.schemas.inspection import (
    FileInfoSchema,
    ContainerInfoSchema,
    VideoStreamInfoSchema,
    AudioStreamInfoSchema,
    StreamSummarySchema,
    VideoInspectionReportResponse
)

router = APIRouter(prefix="/videos", tags=["Surveillance Videos"])


def _format_video_response(video: Video, request: Request, uploader_email: Optional[str] = None) -> VideoResponse:
    base_url = str(request.base_url).rstrip("/")
    stream_url = f"{base_url}/api/v1/videos/{video.id}/stream"
    thumbnail_url = f"{base_url}/api/v1/videos/{video.id}/thumbnail" if video.thumbnail_s3_key else None
    
    email = uploader_email
    if email is None:
        try:
            email = video.uploader.email if video.uploader else None
        except Exception:
            email = None

    return VideoResponse(
        id=video.id,
        title=video.title,
        source_type=getattr(video, "source_type", "UPLOADED") or "UPLOADED",
        description=video.description,
        original_filename=video.original_filename,
        file_size=video.file_size,
        content_type=video.content_type,
        sha256_checksum=video.sha256_checksum,
        status=video.status,
        error_message=video.error_message,
        duration_seconds=video.duration_seconds,
        width=video.width,
        height=video.height,
        fps=video.fps,
        video_codec=video.video_codec,
        audio_codec=video.audio_codec,
        bitrate=video.bitrate,
        thumbnail_url=thumbnail_url,
        stream_url=stream_url,
        uploaded_by=email,
        created_at=video.created_at,
        updated_at=video.updated_at
    )


# -------------------------------------------------------------------------
# Upload Workflow
# -------------------------------------------------------------------------

@router.post(
    "/upload/init",
    response_model=VideoUploadInitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize resumable chunked video upload"
)
async def init_video_upload(
    body: VideoUploadInitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    video_id = uuid.uuid4()
    s3_key = f"videos/{video_id}/{body.filename}"

    video = Video(
        id=video_id,
        title=body.title,
        source_type=body.source_type.upper() if body.source_type else "UPLOADED",
        description=body.description,
        original_filename=body.filename,
        file_size=body.file_size,
        content_type=body.content_type,
        sha256_checksum=body.expected_sha256,
        s3_key=s3_key,
        status=VideoStatus.UPLOADING,
        uploaded_by_id=current_user.id
    )
    db.add(video)

    session_id = uuid.uuid4()
    temp_dir = StorageService.get_upload_temp_dir(str(session_id))
    upload_session = VideoUploadSession(
        id=session_id,
        video_id=video_id,
        total_chunks=body.total_chunks,
        chunk_size=body.chunk_size,
        expected_sha256=body.expected_sha256,
        temp_directory=temp_dir,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
    )
    db.add(upload_session)
    await db.commit()
    await db.refresh(upload_session)

    return VideoUploadInitResponse(
        upload_id=session_id,
        video_id=video_id,
        chunk_size=body.chunk_size,
        total_chunks=body.total_chunks,
        uploaded_chunks=[]
    )


@router.post(
    "/upload/chunk",
    response_model=ChunkUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload and verify individual video chunk"
)
async def upload_video_chunk(
    upload_id: uuid.UUID = Form(...),
    chunk_index: int = Form(...),
    chunk_hash: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Retrieve upload session
    stmt = select(VideoUploadSession).where(VideoUploadSession.id == upload_id)
    res = await db.execute(stmt)
    upload_session = res.scalar_one_or_none()
    if not upload_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload session not found")

    if upload_session.is_completed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload session already completed")

    if chunk_index < 0 or chunk_index >= upload_session.total_chunks:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid chunk index")

    chunk_bytes = await file.read()
    try:
        size, actual_hash = await StorageService.save_chunk(
            upload_id=str(upload_id),
            chunk_index=chunk_index,
            chunk_bytes=chunk_bytes,
            expected_hash=chunk_hash
        )
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))

    # Record chunk in database if not already present
    chunk_stmt = select(VideoChunk).where(
        VideoChunk.upload_session_id == upload_id,
        VideoChunk.chunk_index == chunk_index
    )
    chunk_res = await db.execute(chunk_stmt)
    existing_chunk = chunk_res.scalar_one_or_none()

    if not existing_chunk:
        new_chunk = VideoChunk(
            id=uuid.uuid4(),
            upload_session_id=upload_id,
            chunk_index=chunk_index,
            chunk_size=size,
            sha256_checksum=actual_hash
        )
        db.add(new_chunk)
        upload_session.uploaded_chunks += 1
        await db.commit()

    return ChunkUploadResponse(
        upload_id=upload_id,
        chunk_index=chunk_index,
        status="STORED",
        uploaded_count=upload_session.uploaded_chunks
    )


@router.get(
    "/upload/{upload_id}/status",
    response_model=UploadStatusResponse,
    summary="Query upload progress and list uploaded chunks for resumption"
)
async def get_upload_status(
    upload_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(VideoUploadSession).where(VideoUploadSession.id == upload_id)
    res = await db.execute(stmt)
    upload_session = res.scalar_one_or_none()
    if not upload_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload session not found")

    chunks_stmt = select(VideoChunk.chunk_index).where(VideoChunk.upload_session_id == upload_id)
    chunks_res = await db.execute(chunks_stmt)
    uploaded_indices = [row[0] for row in chunks_res.fetchall()]

    return UploadStatusResponse(
        upload_id=upload_id,
        video_id=upload_session.video_id,
        total_chunks=upload_session.total_chunks,
        uploaded_chunks=uploaded_indices,
        is_completed=upload_session.is_completed
    )


@router.post(
    "/upload/complete",
    response_model=VideoResponse,
    summary="Reassemble chunks, commit to MinIO, and launch media telemetry worker"
)
async def complete_video_upload(
    body: UploadCompleteRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(VideoUploadSession).where(VideoUploadSession.id == body.upload_id)
    res = await db.execute(stmt)
    upload_session = res.scalar_one_or_none()
    if not upload_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload session not found")

    video_stmt = select(Video).where(Video.id == upload_session.video_id)
    video_res = await db.execute(video_stmt)
    video = video_res.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated video not found")

    try:
        total_size, overall_hash, assembled_path = StorageService.assemble_and_upload(
            upload_id=str(body.upload_id),
            total_chunks=upload_session.total_chunks,
            target_s3_key=video.s3_key,
            content_type=video.content_type
        )
    except Exception as exc:
        video.status = VideoStatus.FAILED
        video.error_message = str(exc)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Assembly failed: {exc}")

    # Integrity verification against expected hash if provided
    if body.expected_sha256 and overall_hash.lower() != body.expected_sha256.lower():
        video.status = VideoStatus.FAILED
        video.error_message = f"File hash mismatch: expected {body.expected_sha256}, got {overall_hash}"
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Full file SHA-256 verification failed")

    # Update state
    video.file_size = total_size
    video.sha256_checksum = overall_hash
    video.status = VideoStatus.PROCESSING
    upload_session.is_completed = True
    await db.commit()
    await db.refresh(video)

    # Launch background media processing
    background_tasks.add_task(
        MediaProcessingService.process_video_post_upload,
        video_id=str(video.id),
        upload_id=str(body.upload_id),
        assembled_path=assembled_path
    )

    return _format_video_response(video, request, uploader_email=current_user.email)


# -------------------------------------------------------------------------
# Video Library & Metadata Endpoints
# -------------------------------------------------------------------------

@router.get(
    "",
    response_model=VideoListResponse,
    summary="List, search, and filter archived surveillance videos"
)
@router.get(
    "/",
    response_model=VideoListResponse,
    include_in_schema=False
)
async def list_videos(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=100),
    q: Optional[str] = Query(None, description="Search by title, description or filename"),
    status: Optional[str] = Query(None, description="Filter by status (READY, PROCESSING, etc.)"),
    source_type: Optional[str] = Query(None, description="Filter by source type (LIVE or UPLOADED)"),
    codec: Optional[str] = Query(None, description="Filter by video codec"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Video)

    # Source type filter (LIVE vs UPLOADED)
    if source_type and source_type.upper() != "ALL":
        query = query.where(Video.source_type == source_type.upper())

    # Search filter
    if q:
        search_pattern = f"%{q.strip()}%"
        query = query.where(
            or_(
                Video.title.ilike(search_pattern),
                Video.original_filename.ilike(search_pattern),
                Video.description.ilike(search_pattern)
            )
        )

    # Status filter
    if status and status.upper() != "ALL":
        query = query.where(Video.status == status.upper())

    # Codec filter
    if codec:
        query = query.where(Video.video_codec.ilike(f"%{codec}%"))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(count_query)
    total = total_res.scalar() or 0

    # Paginate and order by newest first
    offset = (page - 1) * limit
    paginated_query = query.order_by(desc(Video.created_at)).offset(offset).limit(limit)
    res = await db.execute(paginated_query)
    videos = res.scalars().all()

    items = [_format_video_response(v, request) for v in videos]
    total_pages = (total + limit - 1) // limit if total > 0 else 1

    return VideoListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )


@router.get(
    "/{video_id}",
    response_model=VideoResponse,
    summary="Get detailed video telemetry and metadata"
)
async def get_video(
    video_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Video).where(Video.id == video_id)
    res = await db.execute(stmt)
    video = res.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    return _format_video_response(video, request)


@router.delete(
    "/{video_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete video from surveillance archive and MinIO"
)
async def delete_video(
    video_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Video).where(Video.id == video_id)
    res = await db.execute(stmt)
    video = res.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    # Delete MinIO objects
    StorageService.delete_video_objects(video.s3_key, video.thumbnail_s3_key)

    await db.delete(video)
    await db.commit()

    return {"message": "Video deleted successfully", "video_id": str(video_id)}


# -------------------------------------------------------------------------
# Range Streaming & Thumbnail Endpoints
# -------------------------------------------------------------------------

@router.get(
    "/{video_id}/stream",
    summary="Stream video with HTTP 206 Partial Content range requests"
)
async def stream_video(
    video_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Video).where(Video.id == video_id)
    res = await db.execute(stmt)
    video = res.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    total_size = video.file_size
    range_header = request.headers.get("range")

    if not range_header:
        # Full content stream (200 OK)
        stream_gen = StorageService.stream_byte_range(video.s3_key, start=0, length=total_size)
        headers = {
            "Content-Length": str(total_size),
            "Content-Type": video.content_type,
            "Accept-Ranges": "bytes",
        }
        return StreamingResponse(stream_gen, status_code=status.HTTP_200_OK, headers=headers)

    # Parse Range: bytes=start-end
    range_match = re.match(r"bytes=(\d+)-(\d*)", range_header)
    if not range_match:
        raise HTTPException(status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE, detail="Invalid Range header")

    start_str, end_str = range_match.groups()
    start = int(start_str)
    end = int(end_str) if end_str else total_size - 1

    if start >= total_size or end >= total_size or start > end:
        raise HTTPException(
            status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
            headers={"Content-Range": f"bytes */{total_size}"}
        )

    content_length = (end - start) + 1
    stream_gen = StorageService.stream_byte_range(video.s3_key, start=start, length=content_length)

    headers = {
        "Content-Range": f"bytes {start}-{end}/{total_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
        "Content-Type": video.content_type,
    }

    return StreamingResponse(stream_gen, status_code=status.HTTP_206_PARTIAL_CONTENT, headers=headers)


@router.get(
    "/{video_id}/thumbnail",
    summary="Serve video scrub preview thumbnail"
)
async def get_video_thumbnail(
    video_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Video).where(Video.id == video_id)
    res = await db.execute(stmt)
    video = res.scalar_one_or_none()
    if not video or not video.thumbnail_s3_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thumbnail not available")

    thumb_gen = StorageService.stream_thumbnail(video.thumbnail_s3_key)
    headers = {
        "Content-Type": "image/jpeg",
        "Cache-Control": "public, max-age=86400",
    }
    return StreamingResponse(thumb_gen, headers=headers)


@router.post(
    "/live/record",
    response_model=VideoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Capture or simulate live CCTV camera stream recording"
)
async def record_live_camera_feed(
    body: LiveCaptureRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    video_id = uuid.uuid4()
    session_id = uuid.uuid4()
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    camera_clean = re.sub(r'[^a-zA-Z0-9_-]', '_', body.camera_id)
    filename = f"live_{camera_clean}_{timestamp_str}.mp4"
    s3_key = f"videos/{video_id}/{filename}"

    temp_dir = StorageService.get_upload_temp_dir(str(session_id))
    os.makedirs(temp_dir, exist_ok=True)
    temp_clip_path = os.path.join(temp_dir, filename)

    duration = min(max(body.duration_seconds, 1), 60)
    title = body.title or f"{body.camera_id} Live Capture ({datetime.now(timezone.utc).strftime('%H:%M:%S UTC')})"

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"testsrc=duration={duration}:size=1280x720:rate=30",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        temp_clip_path
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute camera recording command: {exc}"
        )

    if not os.path.exists(temp_clip_path) or os.path.getsize(temp_clip_path) == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to produce camera recording file"
        )

    file_size = os.path.getsize(temp_clip_path)
    file_sha256 = StorageService.compute_file_sha256(temp_clip_path)

    # Ingest to MinIO
    StorageService.upload_file_to_s3(temp_clip_path, s3_key, content_type="video/mp4")

    # Save Video record
    video = Video(
        id=video_id,
        title=title,
        source_type=VideoSourceType.LIVE,
        description=body.description,
        original_filename=filename,
        file_size=file_size,
        content_type="video/mp4",
        sha256_checksum=file_sha256,
        s3_key=s3_key,
        status=VideoStatus.PROCESSING,
        uploaded_by_id=current_user.id
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)

    background_tasks.add_task(
        MediaProcessingService.process_video_post_upload,
        str(video_id),
        str(session_id),
        temp_clip_path
    )

    return _format_video_response(video, request, uploader_email=current_user.email)


@router.get(
    "/{video_id}/inspection",
    response_model=VideoInspectionReportResponse,
    summary="Retrieve full 5-category FFprobe metadata inspection report"
)
async def get_video_inspection(
    video_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = (
        select(Video)
        .where(Video.id == video_id)
        .options(selectinload(Video.inspections).selectinload(VideoInspection.streams))
    )
    res = await db.execute(stmt)
    video = res.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    if not video.inspections:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media inspection has not been completed for this video yet"
        )

    insp: VideoInspection = video.inspections[0]

    # Category A: File Info
    file_info = FileInfoSchema(
        original_filename=video.original_filename,
        file_size=insp.file_size,
        file_format=insp.file_format,
        sha256_checksum=insp.sha256_checksum,
        upload_timestamp=video.created_at
    )

    # Category B: Container Info
    container_info = ContainerInfoSchema(
        format_name=insp.format_name,
        format_long_name=insp.format_long_name,
        duration_seconds=insp.duration_seconds,
        bitrate=insp.bitrate,
        start_time=insp.start_time,
        container_size=insp.container_size
    )

    # Category C: Video Stream Info
    video_stream = None
    if insp.primary_video_stream_index is not None and insp.video_codec:
        video_stream = VideoStreamInfoSchema(
            stream_index=insp.primary_video_stream_index,
            codec_name=insp.video_codec,
            codec_long_name=insp.video_codec_long_name,
            width=insp.width or 0,
            height=insp.height or 0,
            fps=insp.fps,
            rational_fps=insp.rational_fps,
            pixel_format=insp.pixel_format,
            time_base=insp.time_base,
            start_timestamp=insp.video_start_time,
            duration_seconds=insp.video_duration_seconds or insp.duration_seconds,
            reported_frame_count=insp.reported_frame_count
        )

    # Category D: Audio Stream Info
    audio_stream = AudioStreamInfoSchema(
        has_audio=insp.has_audio,
        stream_index=insp.primary_audio_stream_index,
        codec_name=insp.audio_codec,
        sample_rate=insp.audio_sample_rate,
        channels=insp.audio_channels,
        channel_layout=insp.audio_channel_layout,
        duration_seconds=insp.audio_duration_seconds
    )

    # Category E: Stream Catalog
    all_streams = [
        StreamSummarySchema(
            stream_index=s.stream_index,
            stream_type=s.stream_type,
            codec_name=s.codec_name,
            codec_long_name=s.codec_long_name,
            is_primary=s.is_primary,
            is_default=s.is_default,
            is_attached_pic=s.is_attached_pic,
            width=s.width,
            height=s.height,
            fps=s.fps,
            rational_fps=s.rational_fps,
            pixel_format=s.pixel_format,
            time_base=s.time_base,
            sample_rate=s.sample_rate,
            channels=s.channels,
            channel_layout=s.channel_layout,
            duration_seconds=s.duration_seconds,
            bitrate=s.bitrate,
            disposition=s.disposition,
            stream_metadata=s.stream_metadata
        )
        for s in (insp.streams or [])
    ]

    return VideoInspectionReportResponse(
        inspection_id=insp.id,
        video_id=video.id,
        extractor_version=insp.extractor_version,
        metadata_status=insp.metadata_status,
        validation_status=insp.validation_status,
        error_message=insp.error_message,
        inspected_at=insp.created_at,
        file_info=file_info,
        container_info=container_info,
        video_stream=video_stream,
        audio_stream=audio_stream,
        all_streams=all_streams,
        raw_metadata=insp.raw_ffprobe_json
    )


@router.post(
    "/{video_id}/inspect",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger asynchronous FFprobe media metadata inspection"
)
async def trigger_video_inspection(
    video_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Video).where(Video.id == video_id)
    res = await db.execute(stmt)
    video = res.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    video.metadata_status = "EXTRACTING"
    await db.commit()

    background_tasks.add_task(MetadataInspectionService.inspect_video, video.id)
    return {
        "message": "Media metadata inspection job scheduled",
        "video_id": str(video.id),
        "status": "EXTRACTING"
    }


