from unittest.mock import MagicMock, patch
import pytest
from app.core.config import settings
from app.core.minio_client import MinioClientManager, get_minio_client


def test_minio_client_initialization():
    MinioClientManager._client = None
    with patch("app.core.minio_client.Minio") as mock_minio_class:
        mock_instance = MagicMock()
        mock_minio_class.return_value = mock_instance

        client = get_minio_client()
        assert client is mock_instance
        mock_minio_class.assert_called_once()
        # Verify endpoint and credentials were passed
        call_kwargs = mock_minio_class.call_args[1]
        assert "minioadmin" in call_kwargs["access_key"]
        assert call_kwargs["secure"] == settings.MINIO_SECURE


def test_minio_initialize_buckets():
    MinioClientManager._client = None
    with patch("app.core.minio_client.Minio") as mock_minio_class:
        mock_instance = MagicMock()
        mock_minio_class.return_value = mock_instance
        # Simulate video bucket missing, thumbnail bucket existing
        mock_instance.bucket_exists.side_effect = lambda b: b == settings.MINIO_BUCKET_THUMBNAILS

        MinioClientManager.initialize_buckets()

        # Should check both buckets
        assert mock_instance.bucket_exists.call_count == 2
        # Should make the missing bucket
        mock_instance.make_bucket.assert_called_once_with(settings.MINIO_BUCKET_VIDEOS)
