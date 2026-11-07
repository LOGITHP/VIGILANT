import uuid
import hashlib
from unittest.mock import MagicMock, patch
import pytest
from httpx import AsyncClient
from app.models.user import User


@pytest.mark.asyncio
async def test_video_upload_and_stream_flow(client: AsyncClient, db_session):
    # 1. Register and login a user to get auth token
    await client.post("/api/v1/auth/register", json={
        "email": "cctv_guard@vigilant.ai",
        "password": "Password123!",
        "full_name": "Guard Unit 1"
    })
    login_res = await client.post("/api/v1/auth/login", json={
        "username": "cctv_guard@vigilant.ai",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Init upload
    init_res = await client.post("/api/v1/videos/upload/init", json={
        "title": "East Gate Morning Feed",
        "filename": "east_gate_morning.mp4",
        "file_size": 2048,
        "content_type": "video/mp4",
        "total_chunks": 2,
        "chunk_size": 1024,
        "description": "Perimeter capture"
    }, headers=headers)
    assert init_res.status_code == 201
    init_data = init_res.json()
    upload_id = init_data["upload_id"]
    video_id = init_data["video_id"]
    assert init_data["total_chunks"] == 2

    # 3. Upload chunk 0
    chunk0 = b"A" * 1024
    chunk0_hash = hashlib.sha256(chunk0).hexdigest()
    c0_res = await client.post(
        "/api/v1/videos/upload/chunk",
        data={"upload_id": upload_id, "chunk_index": 0, "chunk_hash": chunk0_hash},
        files={"file": ("0.part", chunk0, "application/octet-stream")},
        headers=headers
    )
    assert c0_res.status_code == 200
    assert c0_res.json()["uploaded_count"] == 1

    # 4. Check status for resumption
    status_res = await client.get(f"/api/v1/videos/upload/{upload_id}/status", headers=headers)
    assert status_res.status_code == 200
    assert 0 in status_res.json()["uploaded_chunks"]

    # 5. Upload chunk 1
    chunk1 = b"B" * 1024
    chunk1_hash = hashlib.sha256(chunk1).hexdigest()
    c1_res = await client.post(
        "/api/v1/videos/upload/chunk",
        data={"upload_id": upload_id, "chunk_index": 1, "chunk_hash": chunk1_hash},
        files={"file": ("1.part", chunk1, "application/octet-stream")},
        headers=headers
    )
    assert c1_res.status_code == 200
    assert c1_res.json()["uploaded_count"] == 2

    # 6. Complete upload with mocked MinIO and background worker
    with patch("app.services.storage_service.get_minio_client") as mock_get_client, \
         patch("app.services.media_service.MediaProcessingService.process_video_post_upload"):
        mock_minio = MagicMock()
        mock_get_client.return_value = mock_minio

        comp_res = await client.post("/api/v1/videos/upload/complete", json={
            "upload_id": upload_id
        }, headers=headers)
        assert comp_res.status_code == 200
        comp_data = comp_res.json()
        assert comp_data["id"] == video_id
        assert comp_data["title"] == "East Gate Morning Feed"

    # 7. List videos and search
    list_res = await client.get("/api/v1/videos?q=East Gate", headers=headers)
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "East Gate Morning Feed"

    # 8. Test range streaming endpoint with Range header (mocking MinIO stream)
    with patch("app.services.storage_service.get_minio_client") as mock_get_client:
        mock_minio = MagicMock()
        mock_stream = MagicMock()
        mock_stream.stream.return_value = [b"A" * 512]
        mock_minio.get_object.return_value = mock_stream
        mock_get_client.return_value = mock_minio

        stream_res = await client.get(
            f"/api/v1/videos/{video_id}/stream",
            headers={"Range": "bytes=0-511"}
        )
        assert stream_res.status_code == 206
        assert stream_res.headers["Content-Range"] == "bytes 0-511/2048"
        assert stream_res.headers["Accept-Ranges"] == "bytes"
