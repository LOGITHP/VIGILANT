import logging
from minio import Minio
from minio.error import S3Error
from app.core.config import settings

logger = logging.getLogger("vigilant.minio")


class MinioClientManager:
    _client: Minio = None

    @classmethod
    def get_client(cls) -> Minio:
        if cls._client is None:
            endpoint = settings.MINIO_ENDPOINT
            # Strip http:// or https:// if present in endpoint
            if endpoint.startswith("http://"):
                endpoint = endpoint[7:]
            elif endpoint.startswith("https://"):
                endpoint = endpoint[8:]

            cls._client = Minio(
                endpoint=endpoint,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
            )
        return cls._client

    @classmethod
    def initialize_buckets(cls) -> None:
        """Ensure required buckets exist; creates them if absent."""
        client = cls.get_client()
        required_buckets = [
            settings.MINIO_BUCKET_VIDEOS,
            settings.MINIO_BUCKET_THUMBNAILS,
        ]
        for bucket in required_buckets:
            try:
                if not client.bucket_exists(bucket):
                    client.make_bucket(bucket)
                    logger.info("MinIO bucket created: %s", bucket)
                else:
                    logger.info("MinIO bucket already exists: %s", bucket)
            except S3Error as e:
                logger.error("Failed to check/create MinIO bucket %s: %s", bucket, e)
                raise


def get_minio_client() -> Minio:
    return MinioClientManager.get_client()
