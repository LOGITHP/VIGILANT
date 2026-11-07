import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Integer, BigInteger, Float, Text, JSON, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class VideoStatus:
    UPLOADING = "UPLOADING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False
    )
    content_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="video/mp4"
    )
    sha256_checksum: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True
    )
    s3_key: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        unique=True
    )
    thumbnail_s3_key: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=VideoStatus.UPLOADING,
        index=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # FFprobe Extracted Telemetry
    duration_seconds: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    width: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    height: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    fps: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    video_codec: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    audio_codec: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    bitrate: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True
    )
    raw_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )

    # Ownership & Timestamps
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    uploader: Mapped[Optional["User"]] = relationship(lazy="selectin")
    upload_sessions: Mapped[List["VideoUploadSession"]] = relationship(
        back_populates="video",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class VideoUploadSession(Base):
    __tablename__ = "video_upload_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    video_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    total_chunks: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    chunk_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5242880  # 5MB
    )
    uploaded_chunks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )
    expected_sha256: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True
    )
    temp_directory: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    # Relationships
    video: Mapped["Video"] = relationship(back_populates="upload_sessions")
    chunks: Mapped[List["VideoChunk"]] = relationship(
        back_populates="upload_session",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class VideoChunk(Base):
    __tablename__ = "video_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    upload_session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("video_upload_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    chunk_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    sha256_checksum: Mapped[str] = mapped_column(
        String(64),
        nullable=False
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    upload_session: Mapped["VideoUploadSession"] = relationship(back_populates="chunks")
