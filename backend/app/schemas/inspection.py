from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class FileInfoSchema(BaseModel):
    original_filename: str = Field(..., description="Uploaded video filename")
    file_size: int = Field(..., description="File size in bytes")
    file_format: Optional[str] = Field(None, description="Identified format string")
    sha256_checksum: Optional[str] = Field(None, description="SHA-256 cryptographic hash")
    upload_timestamp: datetime = Field(..., description="Timestamp when file was uploaded")


class ContainerInfoSchema(BaseModel):
    format_name: Optional[str] = Field(None, description="Container short format name (e.g. mp4, matroska)")
    format_long_name: Optional[str] = Field(None, description="Full human-readable container format name")
    duration_seconds: Optional[float] = Field(None, description="Container-level duration in seconds")
    bitrate: Optional[int] = Field(None, description="Container-level average bitrate in bps")
    start_time: Optional[float] = Field(None, description="Presentation start time")
    container_size: Optional[int] = Field(None, description="Byte size reported in container header")


class VideoStreamInfoSchema(BaseModel):
    stream_index: int = Field(..., description="Zero-based stream index in container")
    codec_name: str = Field(..., description="Video codec name (e.g. h264, hevc, mjpeg)")
    codec_long_name: Optional[str] = Field(None, description="Full video codec name")
    width: int = Field(..., description="Frame width in pixels")
    height: int = Field(..., description="Frame height in pixels")
    fps: Optional[float] = Field(None, description="Calculated average frame rate (FPS)")
    rational_fps: Optional[str] = Field(None, description="Exact rational frame rate (e.g. 30000/1001, 25/1)")
    pixel_format: Optional[str] = Field(None, description="Chroma format (e.g. yuv420p, nv12)")
    time_base: Optional[str] = Field(None, description="Stream time base fraction (e.g. 1/90000)")
    start_timestamp: Optional[float] = Field(None, description="Stream start timestamp")
    duration_seconds: Optional[float] = Field(None, description="Stream-level duration in seconds")
    reported_frame_count: Optional[int] = Field(None, description="Total frame count if reported by container")


class AudioStreamInfoSchema(BaseModel):
    has_audio: bool = Field(False, description="Whether container contains a valid audio stream")
    stream_index: Optional[int] = Field(None, description="Audio stream index")
    codec_name: Optional[str] = Field(None, description="Audio codec name (e.g. aac, opus, pcm_alaw)")
    sample_rate: Optional[int] = Field(None, description="Audio sampling rate in Hz (e.g. 48000, 44100)")
    channels: Optional[int] = Field(None, description="Audio channel count (e.g. 1, 2)")
    channel_layout: Optional[str] = Field(None, description="Channel layout designation (e.g. stereo, mono)")
    duration_seconds: Optional[float] = Field(None, description="Audio stream duration in seconds")


class StreamSummarySchema(BaseModel):
    stream_index: int = Field(..., description="Stream index in container")
    stream_type: str = Field(..., description="Stream type: video, audio, subtitle, data, attachment")
    codec_name: Optional[str] = Field(None, description="Codec name")
    codec_long_name: Optional[str] = Field(None, description="Full codec name")
    is_primary: bool = Field(False, description="True if selected as primary stream")
    is_default: bool = Field(False, description="True if marked as default stream")
    is_attached_pic: bool = Field(False, description="True if stream is static cover art or thumbnail")
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    rational_fps: Optional[str] = None
    pixel_format: Optional[str] = None
    time_base: Optional[str] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    channel_layout: Optional[str] = None
    duration_seconds: Optional[float] = None
    bitrate: Optional[int] = None
    disposition: Optional[Dict[str, Any]] = None
    stream_metadata: Optional[Dict[str, Any]] = None


class VideoInspectionReportResponse(BaseModel):
    inspection_id: UUID
    video_id: UUID
    extractor_version: str = "1.0.0"
    metadata_status: str = Field(..., description="EXTRACTING | COMPLETED | FAILED")
    validation_status: str = Field(..., description="PENDING | VALIDATED | INVALID")
    error_message: Optional[str] = None
    inspected_at: datetime

    # 5 Extracted Categories
    file_info: FileInfoSchema
    container_info: ContainerInfoSchema
    video_stream: Optional[VideoStreamInfoSchema] = None
    audio_stream: AudioStreamInfoSchema
    all_streams: List[StreamSummarySchema] = []

    # Raw FFprobe output (optional)
    raw_metadata: Optional[Dict[str, Any]] = None
