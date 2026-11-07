import os
import shutil
import hashlib
import logging
from io import BytesIO
from typing import Tuple, Generator, Optional
from minio.error import S3Error
from app.core.config import settings
from app.core.minio_client import get_minio_client

logger = logging.getLogger("vigilant.storage")


class StorageService:

    @staticmethod
    def get_upload_temp_dir(upload_id: str) -> str:
        temp_dir = os.path.join(settings.UPLOAD_TEMP_DIR, str(upload_id))
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

    @classmethod
    async def save_chunk(
        cls,
        upload_id: str,
        chunk_index: int,
        chunk_bytes: bytes,
        expected_hash: Optional[str] = None
    ) -> Tuple[int, str]:
        """Save a single video chunk to disk and verify SHA-256 hash."""
        actual_hash = hashlib.sha256(chunk_bytes).hexdigest()

        if expected_hash and actual_hash.lower() != expected_hash.lower():
            raise ValueError(
                f"Chunk {chunk_index} checksum mismatch: expected {expected_hash}, got {actual_hash}"
            )

        temp_dir = cls.get_upload_temp_dir(upload_id)
        chunk_path = os.path.join(temp_dir, f"{chunk_index}.part")

        # Write chunk bytes atomically
        with open(chunk_path, "wb") as f:
            f.write(chunk_bytes)

        return len(chunk_bytes), actual_hash

    @classmethod
    def assemble_and_upload(
        cls,
        upload_id: str,
        total_chunks: int,
        target_s3_key: str,
        content_type: str = "video/mp4",
        bucket_name: Optional[str] = None
    ) -> Tuple[int, str, str]:
        """
        Assemble chunks in sequential order, compute overall SHA-256 checksum,
        upload to MinIO, and return (file_size, sha256_hash, assembled_temp_path).
        """
        bucket = bucket_name or settings.MINIO_BUCKET_VIDEOS
        temp_dir = cls.get_upload_temp_dir(upload_id)
        assembled_path = os.path.join(temp_dir, "assembled.mp4")

        hasher = hashlib.sha256()
        total_bytes = 0

        # Verify all parts exist before assembly
        for i in range(total_chunks):
            part_path = os.path.join(temp_dir, f"{i}.part")
            if not os.path.exists(part_path):
                raise FileNotFoundError(f"Missing chunk {i} of {total_chunks} for upload {upload_id}")

        # Assemble and hash simultaneously
        with open(assembled_path, "wb") as outfile:
            for i in range(total_chunks):
                part_path = os.path.join(temp_dir, f"{i}.part")
                with open(part_path, "rb") as infile:
                    while chunk := infile.read(65536):
                        hasher.update(chunk)
                        outfile.write(chunk)
                        total_bytes += len(chunk)

        overall_hash = hasher.hexdigest()

        # Upload assembled file to MinIO
        minio_client = get_minio_client()
        try:
            minio_client.fput_object(
                bucket_name=bucket,
                object_name=target_s3_key,
                file_path=assembled_path,
                content_type=content_type
            )
            logger.info(
                "Successfully uploaded %s to MinIO (%d bytes, SHA256: %s)",
                target_s3_key, total_bytes, overall_hash
            )
        except S3Error as e:
            logger.error("MinIO upload failed for %s: %s", target_s3_key, e)
            raise

        # Clean up chunk parts, leave assembled file for post-processing worker if needed
        for i in range(total_chunks):
            part_path = os.path.join(temp_dir, f"{i}.part")
            try:
                os.remove(part_path)
            except OSError:
                pass

        return total_bytes, overall_hash, assembled_path

    @classmethod
    def clean_upload_dir(cls, upload_id: str) -> None:
        """Remove temporary directory for this upload."""
        temp_dir = os.path.join(settings.UPLOAD_TEMP_DIR, str(upload_id))
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

    @classmethod
    def get_object_stat(cls, s3_key: str, bucket_name: Optional[str] = None):
        """Retrieve MinIO object metadata/size."""
        bucket = bucket_name or settings.MINIO_BUCKET_VIDEOS
        minio_client = get_minio_client()
        return minio_client.stat_object(bucket, s3_key)

    @classmethod
    def stream_byte_range(
        cls,
        s3_key: str,
        start: int,
        length: int,
        bucket_name: Optional[str] = None,
        chunk_buffer_size: int = 65536
    ) -> Generator[bytes, None, None]:
        """Stream byte range slice directly from MinIO without loading whole file."""
        bucket = bucket_name or settings.MINIO_BUCKET_VIDEOS
        minio_client = get_minio_client()
        response = None
        try:
            response = minio_client.get_object(
                bucket_name=bucket,
                object_name=s3_key,
                offset=start,
                length=length
            )
            for data in response.stream(chunk_buffer_size):
                yield data
        finally:
            if response is not None:
                response.close()
                response.release_conn()

    @classmethod
    def upload_thumbnail(
        cls,
        thumbnail_key: str,
        image_bytes: bytes,
        content_type: str = "image/jpeg"
    ) -> str:
        """Upload thumbnail image to MinIO thumbnail bucket."""
        minio_client = get_minio_client()
        bucket = settings.MINIO_BUCKET_THUMBNAILS
        data_stream = BytesIO(image_bytes)
        minio_client.put_object(
            bucket_name=bucket,
            object_name=thumbnail_key,
            data=data_stream,
            length=len(image_bytes),
            content_type=content_type
        )
        return thumbnail_key

    @classmethod
    def stream_thumbnail(cls, thumbnail_key: str) -> Generator[bytes, None, None]:
        """Stream thumbnail from MinIO thumbnail bucket."""
        bucket = settings.MINIO_BUCKET_THUMBNAILS
        minio_client = get_minio_client()
        response = None
        try:
            response = minio_client.get_object(bucket, thumbnail_key)
            for data in response.stream(32768):
                yield data
        finally:
            if response is not None:
                response.close()
                response.release_conn()

    @classmethod
    def delete_video_objects(cls, s3_key: str, thumbnail_s3_key: Optional[str] = None) -> None:
        """Delete video and thumbnail objects from MinIO."""
        minio_client = get_minio_client()
        try:
            minio_client.remove_object(settings.MINIO_BUCKET_VIDEOS, s3_key)
        except Exception as e:
            logger.warning("Could not delete video object %s: %s", s3_key, e)

        if thumbnail_s3_key:
            try:
                minio_client.remove_object(settings.MINIO_BUCKET_THUMBNAILS, thumbnail_s3_key)
            except Exception as e:
                logger.warning("Could not delete thumbnail object %s: %s", thumbnail_s3_key, e)
