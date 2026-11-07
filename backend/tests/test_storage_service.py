import os
import hashlib
from unittest.mock import MagicMock, patch
import pytest
from app.services.storage_service import StorageService


@pytest.mark.asyncio
async def test_save_chunk_success_and_hash_validation(tmp_path):
    upload_id = "test_upload_1"
    chunk_bytes = b"Hello, Surveillance Chunk 0!"
    expected_hash = hashlib.sha256(chunk_bytes).hexdigest()

    with patch("app.services.storage_service.settings.UPLOAD_TEMP_DIR", str(tmp_path)):
        # 1. Successful save
        size, actual_hash = await StorageService.save_chunk(
            upload_id=upload_id,
            chunk_index=0,
            chunk_bytes=chunk_bytes,
            expected_hash=expected_hash
        )
        assert size == len(chunk_bytes)
        assert actual_hash == expected_hash

        # 2. Checksum mismatch should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            await StorageService.save_chunk(
                upload_id=upload_id,
                chunk_index=1,
                chunk_bytes=b"Corrupted bytes",
                expected_hash=expected_hash
            )
        assert "checksum mismatch" in str(exc_info.value)


def test_assemble_and_upload(tmp_path):
    upload_id = "test_upload_assembly"
    part1 = b"AAAA" * 1000
    part2 = b"BBBB" * 1000
    combined = part1 + part2
    expected_combined_hash = hashlib.sha256(combined).hexdigest()

    with patch("app.services.storage_service.settings.UPLOAD_TEMP_DIR", str(tmp_path)), \
         patch("app.services.storage_service.get_minio_client") as mock_get_client:
        mock_minio = MagicMock()
        mock_get_client.return_value = mock_minio

        # Write 2 parts
        temp_dir = StorageService.get_upload_temp_dir(upload_id)
        with open(os.path.join(temp_dir, "0.part"), "wb") as f:
            f.write(part1)
        with open(os.path.join(temp_dir, "1.part"), "wb") as f:
            f.write(part2)

        total_bytes, overall_hash, assembled_path = StorageService.assemble_and_upload(
            upload_id=upload_id,
            total_chunks=2,
            target_s3_key="videos/test.mp4",
            content_type="video/mp4"
        )

        assert total_bytes == len(combined)
        assert overall_hash == expected_combined_hash
        assert os.path.exists(assembled_path)
        mock_minio.fput_object.assert_called_once()


def test_stream_byte_range():
    with patch("app.services.storage_service.get_minio_client") as mock_get_client:
        mock_minio = MagicMock()
        mock_response = MagicMock()
        mock_response.stream.return_value = [b"chunk1", b"chunk2"]
        mock_minio.get_object.return_value = mock_response
        mock_get_client.return_value = mock_minio

        chunks = list(StorageService.stream_byte_range("videos/test.mp4", start=0, length=100))
        assert chunks == [b"chunk1", b"chunk2"]
        mock_minio.get_object.assert_called_once_with(
            bucket_name="vigilant-videos",
            object_name="videos/test.mp4",
            offset=0,
            length=100
        )
        mock_response.close.assert_called_once()

