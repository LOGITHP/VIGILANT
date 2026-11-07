import os
import uuid
import json
import shutil
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from contextlib import nullcontext
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.minio_client import get_minio_client
from app.db.session import AsyncSessionLocal
from app.models.video import (
    Video,
    VideoInspection,
    VideoStream,
    MetadataStatus,
    ValidationStatus
)
from app.services.metadata_normalizer import MetadataNormalizer

logger = logging.getLogger("vigilant.inspection")


class MetadataInspectionService:
    _semaphore: Optional[asyncio.Semaphore] = None

    @classmethod
    def _get_semaphore(cls) -> asyncio.Semaphore:
        if cls._semaphore is None:
            cls._semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_INSPECTIONS)
        return cls._semaphore

    @classmethod
    async def run_ffprobe(cls, file_path: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute FFprobe in an asynchronous subprocess with 120-second timeout.
        Extracts format, stream descriptors, and disposition tags in JSON format.
        """
        exec_timeout = timeout or settings.FFPROBE_TIMEOUT_SECONDS
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            "-show_error",
            file_path
        ]

        logger.debug("Executing ffprobe on %s (timeout=%ds)", file_path, exec_timeout)
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=exec_timeout)

            if proc.returncode != 0:
                err_text = stderr.decode(errors="replace").strip()
                raise RuntimeError(f"FFprobe process failed with exit code {proc.returncode}: {err_text}")

            output_text = stdout.decode(errors="replace")
            if not output_text.strip():
                raise RuntimeError("FFprobe returned empty output")

            return json.loads(output_text)

        except asyncio.TimeoutError:
            logger.error("FFprobe timed out after %ds for file: %s", exec_timeout, file_path)
            raise TimeoutError(f"FFprobe execution exceeded timeout limit of {exec_timeout} seconds")
        except json.JSONDecodeError as e:
            logger.error("Failed to parse FFprobe JSON output: %s", e)
            raise ValueError(f"Malformed FFprobe output: {e}")

    @classmethod
    async def inspect_video(
        cls,
        video_id: uuid.UUID,
        staged_file_path: Optional[str] = None,
        db_session: Optional[AsyncSession] = None
    ) -> Optional[VideoInspection]:
        """
        Main pipeline: runs FFprobe inspection on staged footage or retrieves from MinIO,
        normalizes telemetry across 5 categories, and persists inspection results in PostgreSQL.
        Enforces max 2 concurrent executions via asyncio.Semaphore.
        """
        sem = cls._get_semaphore()
        logger.info("Queued inspection for video %s (concurrency limit=%d)", video_id, settings.MAX_CONCURRENT_INSPECTIONS)

        async with sem:
            logger.info("Acquired inspection slot for video %s", video_id)
            job_id = uuid.uuid4()
            temp_dir = os.path.join(settings.INSPECTION_TEMP_DIR, str(job_id))
            should_cleanup_temp_dir = False

            session_cm = nullcontext(db_session) if db_session is not None else AsyncSessionLocal()
            async with session_cm as db:
                stmt = select(Video).where(Video.id == video_id)
                res = await db.execute(stmt)
                video = res.scalar_one_or_none()

                if not video:
                    logger.error("Video %s not found for inspection", video_id)
                    return None

                video.metadata_status = MetadataStatus.EXTRACTING
                await db.commit()

                try:
                    if staged_file_path and os.path.exists(staged_file_path):
                        local_file_path = staged_file_path
                    else:
                        os.makedirs(temp_dir, exist_ok=True)
                        should_cleanup_temp_dir = True
                        local_file_path = os.path.join(temp_dir, os.path.basename(video.s3_key))
                        minio = get_minio_client()
                        logger.info("Staging video from MinIO: %s -> %s", video.s3_key, local_file_path)
                        minio.fget_object(
                            bucket_name=settings.MINIO_BUCKET_VIDEOS,
                            object_name=video.s3_key,
                            file_path=local_file_path
                        )

                    file_size = os.path.getsize(local_file_path)

                    # 2. Run FFprobe subprocess inspection
                    probe_data = await cls.run_ffprobe(local_file_path)

                    format_dict = probe_data.get("format") or {}
                    streams = probe_data.get("streams") or []

                    # 3. Intelligent Stream Selection
                    primary_video = MetadataNormalizer.select_primary_video_stream(streams)
                    primary_audio = MetadataNormalizer.select_primary_audio_stream(streams)

                    primary_video_idx = MetadataNormalizer.parse_int_safe(primary_video.get("index")) if primary_video else None
                    primary_audio_idx = MetadataNormalizer.parse_int_safe(primary_audio.get("index")) if primary_audio else None

                    # Category B: Container extraction
                    format_name = format_dict.get("format_name")
                    format_long_name = format_dict.get("format_long_name")
                    container_duration = MetadataNormalizer.parse_float_safe(format_dict.get("duration"))
                    container_bitrate = MetadataNormalizer.parse_int_safe(format_dict.get("bit_rate"))
                    start_time = MetadataNormalizer.parse_float_safe(format_dict.get("start_time"))
                    container_size = MetadataNormalizer.parse_int_safe(format_dict.get("size")) or file_size

                    # Category C: Primary Video Stream
                    v_codec = primary_video.get("codec_name") if primary_video else None
                    v_codec_long = primary_video.get("codec_long_name") if primary_video else None
                    v_width = MetadataNormalizer.parse_int_safe(primary_video.get("width")) if primary_video else None
                    v_height = MetadataNormalizer.parse_int_safe(primary_video.get("height")) if primary_video else None
                    v_pix_fmt = primary_video.get("pix_fmt") if primary_video else None
                    v_time_base = primary_video.get("time_base") if primary_video else None
                    v_start_time = MetadataNormalizer.parse_float_safe(primary_video.get("start_time")) if primary_video else None
                    v_duration = MetadataNormalizer.parse_float_safe(primary_video.get("duration")) if primary_video else container_duration
                    v_nb_frames = MetadataNormalizer.parse_int_safe(primary_video.get("nb_frames")) if primary_video else None

                    v_fps, v_rational_fps = (None, None)
                    if primary_video:
                        v_fps, v_rational_fps = MetadataNormalizer.parse_rational_number(
                            primary_video.get("r_frame_rate") or primary_video.get("avg_frame_rate")
                        )

                    # Category D: Primary Audio Stream
                    has_audio = primary_audio is not None
                    a_codec = primary_audio.get("codec_name") if primary_audio else None
                    a_sample_rate = MetadataNormalizer.parse_int_safe(primary_audio.get("sample_rate")) if primary_audio else None
                    a_channels = MetadataNormalizer.parse_int_safe(primary_audio.get("channels")) if primary_audio else None
                    a_layout = primary_audio.get("channel_layout") if primary_audio else None
                    a_duration = MetadataNormalizer.parse_float_safe(primary_audio.get("duration")) if primary_audio else None

                    # Category E: Stream Catalog
                    stream_catalog = MetadataNormalizer.build_stream_catalog(
                        streams,
                        primary_video_idx=primary_video_idx,
                        primary_audio_idx=primary_audio_idx
                    )

                    # 4. Persist VideoInspection Record
                    inspection = VideoInspection(
                        id=uuid.uuid4(),
                        video_id=video_id,
                        extractor_version="1.0.0",
                        metadata_status=MetadataStatus.COMPLETED,
                        validation_status=ValidationStatus.PENDING,
                        error_message=None,
                        file_size=file_size,
                        file_format=format_name,
                        sha256_checksum=video.sha256_checksum,
                        format_name=format_name,
                        format_long_name=format_long_name,
                        duration_seconds=container_duration,
                        bitrate=container_bitrate,
                        start_time=start_time,
                        container_size=container_size,
                        primary_video_stream_index=primary_video_idx,
                        video_codec=v_codec,
                        video_codec_long_name=v_codec_long,
                        width=v_width,
                        height=v_height,
                        fps=v_fps,
                        rational_fps=v_rational_fps,
                        pixel_format=v_pix_fmt,
                        time_base=v_time_base,
                        video_start_time=v_start_time,
                        video_duration_seconds=v_duration,
                        reported_frame_count=v_nb_frames,
                        has_audio=has_audio,
                        primary_audio_stream_index=primary_audio_idx,
                        audio_codec=a_codec,
                        audio_sample_rate=a_sample_rate,
                        audio_channels=a_channels,
                        audio_channel_layout=a_layout,
                        audio_duration_seconds=a_duration,
                        raw_ffprobe_json=probe_data
                    )
                    db.add(inspection)
                    await db.flush()

                    # 5. Persist Stream Records
                    for st_item in stream_catalog:
                        stream_model = VideoStream(
                            id=uuid.uuid4(),
                            inspection_id=inspection.id,
                            stream_index=st_item["stream_index"],
                            stream_type=st_item["stream_type"],
                            codec_name=st_item["codec_name"],
                            codec_long_name=st_item["codec_long_name"],
                            is_primary=st_item["is_primary"],
                            is_default=st_item["is_default"],
                            is_attached_pic=st_item["is_attached_pic"],
                            width=st_item["width"],
                            height=st_item["height"],
                            fps=st_item["fps"],
                            rational_fps=st_item["rational_fps"],
                            pixel_format=st_item["pixel_format"],
                            time_base=st_item["time_base"],
                            sample_rate=st_item["sample_rate"],
                            channels=st_item["channels"],
                            channel_layout=st_item["channel_layout"],
                            duration_seconds=st_item["duration_seconds"],
                            bitrate=st_item["bitrate"],
                            disposition=st_item["disposition"],
                            stream_metadata=st_item["stream_metadata"]
                        )
                        db.add(stream_model)

                    # 6. Update Video summary columns
                    video.duration_seconds = container_duration
                    video.width = v_width
                    video.height = v_height
                    video.fps = v_fps
                    video.video_codec = v_codec
                    video.audio_codec = a_codec
                    video.bitrate = container_bitrate
                    video.metadata_status = MetadataStatus.COMPLETED
                    video.validation_status = ValidationStatus.PENDING

                    await db.commit()

                    insp_stmt = (
                        select(VideoInspection)
                        .where(VideoInspection.id == inspection.id)
                        .options(selectinload(VideoInspection.streams))
                    )
                    insp_res = await db.execute(insp_stmt)
                    refreshed_inspection = insp_res.scalar_one()

                    logger.info("Successfully completed inspection for video %s (%s, %dx%d, %s fps)",
                                video_id, v_codec, v_width or 0, v_height or 0, v_fps or "N/A")
                    return refreshed_inspection

                except Exception as exc:
                    logger.exception("Failed during media inspection for video %s: %s", video_id, exc)
                    video.metadata_status = MetadataStatus.FAILED
                    video.error_message = f"Metadata extraction failed: {str(exc)}"

                    failed_inspection = VideoInspection(
                        id=uuid.uuid4(),
                        video_id=video_id,
                        extractor_version="1.0.0",
                        metadata_status=MetadataStatus.FAILED,
                        validation_status=ValidationStatus.PENDING,
                        error_message=str(exc),
                        file_size=video.file_size,
                        has_audio=False
                    )
                    db.add(failed_inspection)
                    await db.commit()
                    return failed_inspection

                finally:
                    # Clean up temporary sandbox if created
                    if should_cleanup_temp_dir:
                        shutil.rmtree(temp_dir, ignore_errors=True)
                        logger.debug("Cleaned up inspection workspace %s", temp_dir)
