import re
import uuid
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
from app.models.video import Video, VideoUploadSession, VideoChunk, VideoStatus
from app.services.storage_service import StorageService
from app.services.media_service import MediaProcessingService
from app.schemas.video import (
    VideoUploadInitRequest,
    VideoUploadInitResponse,
    ChunkUploadResponse,
    UploadStatusResponse,
    UploadCompleteRequest,
    VideoResponse,
    VideoListResponse
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
    codec: Optional[str] = Query(None, description="Filter by video codec"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Video)

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
