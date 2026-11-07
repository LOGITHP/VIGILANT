from uuid import UUID
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class VideoUploadInitRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Video title or camera identifier")
    filename: str = Field(..., min_length=1, max_length=255, description="Original filename with extension")
    file_size: int = Field(..., gt=0, description="Total size in bytes")
    content_type: str = Field("video/mp4", description="MIME content type")
    total_chunks: int = Field(..., gt=0, description="Total number of chunks")
    chunk_size: int = Field(5242880, gt=0, description="Chunk size in bytes (default 5MB)")
    source_type: str = Field("UPLOADED", description="Source category: LIVE or UPLOADED")
    description: Optional[str] = Field(None, max_length=1000, description="Surveillance notes")
    expected_sha256: Optional[str] = Field(None, min_length=64, max_length=64, description="Pre-computed file hash")


class VideoUploadInitResponse(BaseModel):
    upload_id: UUID
    video_id: UUID
    chunk_size: int
    total_chunks: int
    uploaded_chunks: List[int] = []


class ChunkUploadResponse(BaseModel):
    upload_id: UUID
    chunk_index: int
    status: str = "STORED"
    uploaded_count: int


class UploadStatusResponse(BaseModel):
    upload_id: UUID
    video_id: UUID
    total_chunks: int
    uploaded_chunks: List[int]
    is_completed: bool


class UploadCompleteRequest(BaseModel):
    upload_id: UUID
    expected_sha256: Optional[str] = None


class LiveCaptureRequest(BaseModel):
    camera_id: str = Field("CAM-01", description="Identifier of the live camera feed")
    title: Optional[str] = Field(None, description="Optional custom title")
    duration_seconds: int = Field(4, ge=1, le=60, description="Clip duration in seconds")
    description: Optional[str] = Field("Captured from live surveillance stream", description="Incident notes")



class VideoResponse(BaseModel):
    id: UUID
    title: str
    source_type: str = "UPLOADED"
    description: Optional[str] = None
    original_filename: str
    file_size: int
    content_type: str
    sha256_checksum: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    duration_seconds: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    video_codec: Optional[str] = None
    audio_codec: Optional[str] = None
    bitrate: Optional[int] = None
    thumbnail_url: Optional[str] = None
    stream_url: str
    uploaded_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class VideoListResponse(BaseModel):
    items: List[VideoResponse]
    total: int
    page: int
    limit: int
    total_pages: int

