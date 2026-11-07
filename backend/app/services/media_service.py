import os
import json
import asyncio
import logging
import subprocess
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.video import Video, VideoStatus
from app.services.storage_service import StorageService
from sqlalchemy import select

logger = logging.getLogger("vigilant.media")


class MediaProcessingService:

    @classmethod
    def extract_metadata(cls, file_path: str) -> Dict[str, Any]:
        """Execute ffprobe and parse container, video, and audio streams."""
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path
        ]

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            data = json.loads(result.stdout)
        except Exception as e:
            logger.warning("ffprobe command failed or returned non-zero (%s). Using fallback metadata.", e)
            return {
                "duration_seconds": None,
                "width": None,
                "height": None,
                "fps": None,
                "video_codec": None,
                "audio_codec": None,
                "bitrate": None,
                "raw_metadata": None
            }

        fmt = data.get("format", {})
        streams = data.get("streams", [])

        # Duration & Bitrate
        duration_sec = None
        if "duration" in fmt:
            try:
                duration_sec = round(float(fmt["duration"]), 2)
            except (ValueError, TypeError):
                pass

        bitrate = None
        if "bit_rate" in fmt:
            try:
                bitrate = int(fmt["bit_rate"])
            except (ValueError, TypeError):
                pass

        # Video stream
        video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
        audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

        width = video_stream.get("width") if video_stream else None
        height = video_stream.get("height") if video_stream else None
        video_codec = video_stream.get("codec_name") if video_stream else None
        audio_codec = audio_stream.get("codec_name") if audio_stream else None

        # FPS calculation
        fps = None
        if video_stream and "r_frame_rate" in video_stream:
            r_rate = video_stream["r_frame_rate"]
            try:
                if "/" in r_rate:
                    num, den = r_rate.split("/")
                    if float(den) > 0:
                        fps = round(float(num) / float(den), 2)
                else:
                    fps = round(float(r_rate), 2)
            except Exception:
                pass

        return {
            "duration_seconds": duration_sec,
            "width": width,
            "height": height,
            "fps": fps,
            "video_codec": video_codec,
            "audio_codec": audio_codec,
            "bitrate": bitrate,
            "raw_metadata": data
        }

    @classmethod
    def generate_thumbnail(cls, file_path: str, timestamp_sec: float = 1.0) -> Optional[bytes]:
        """Extract a single frame as JPEG using ffmpeg."""
        seek_str = f"{timestamp_sec:.2f}"
        cmd = [
            "ffmpeg",
            "-y",
            "-ss", seek_str,
            "-i", file_path,
            "-vframes", "1",
            "-q:v", "2",
            "-vf", "scale=640:-1",
            "-f", "image2pipe",
            "-vcodec", "mjpeg",
            "-"
        ]

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            return result.stdout if len(result.stdout) > 0 else None
        except Exception as e:
            logger.warning("ffmpeg thumbnail extraction failed: %s", e)
            return None

    @classmethod
    async def process_video_post_upload(
        cls,
        video_id: str,
        upload_id: str,
        assembled_path: str
    ) -> None:
        """Background worker: extract FFprobe telemetry, generate thumbnail, and update DB."""
        logger.info("Starting post-upload media processing for video %s", video_id)

        async with AsyncSessionLocal() as db:
            stmt = select(Video).where(Video.id == video_id)
            res = await db.execute(stmt)
            video = res.scalar_one_or_none()

            if not video:
                logger.error("Video record %s not found for post-processing", video_id)
                StorageService.clean_upload_dir(upload_id)
                return

            try:
                video.status = VideoStatus.PROCESSING
                await db.commit()

                # 1. Run ffprobe
                meta = cls.extract_metadata(assembled_path)
                video.duration_seconds = meta["duration_seconds"]
                video.width = meta["width"]
                video.height = meta["height"]
                video.fps = meta["fps"]
                video.video_codec = meta["video_codec"]
                video.audio_codec = meta["audio_codec"]
                video.bitrate = meta["bitrate"]
                video.raw_metadata = meta["raw_metadata"]

                # 2. Run ffmpeg thumbnail extraction (1s or 10% of duration)
                seek_time = 1.0
                if meta["duration_seconds"] and meta["duration_seconds"] > 2.0:
                    seek_time = min(meta["duration_seconds"] * 0.1, 5.0)

                thumb_bytes = cls.generate_thumbnail(assembled_path, timestamp_sec=seek_time)
                if thumb_bytes:
                    thumb_key = f"thumbnails/{video_id}.jpg"
                    StorageService.upload_thumbnail(thumb_key, thumb_bytes)
                    video.thumbnail_s3_key = thumb_key

                video.status = VideoStatus.READY
                video.updated_at = datetime.now(timezone.utc)
                await db.commit()
                logger.info("Video %s successfully processed and marked READY", video_id)

                # 3. Execute Phase 3.1.1 full structured media inspection
                try:
                    from app.services.metadata_extractor import MetadataInspectionService
                    await MetadataInspectionService.inspect_video(video.id, staged_file_path=assembled_path)
                    logger.info("Video %s completed full 5-category metadata inspection", video_id)
                except Exception as insp_exc:
                    logger.warning("Secondary metadata inspection failed for video %s: %s", video_id, insp_exc)

            except Exception as exc:
                logger.error("Media processing failed for video %s: %s", video_id, exc)
                video.status = VideoStatus.FAILED
                video.error_message = str(exc)
                await db.commit()
            finally:
                # Clean up assembled temp file & directory
                StorageService.clean_upload_dir(upload_id)
