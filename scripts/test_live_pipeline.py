import os
import time
import math
import hashlib
import requests

BASE_URL = "http://localhost:8000/api/v1"
TEST_VIDEO_PATH = "sample_surveillance.mp4"

def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def compute_file_sha256(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def run_tests():
    print("==================================================")
    print("  VIGILANT - Live Container Integration Test Suite")
    print("==================================================")
    
    # Step 1: Authentication
    print("\n[TEST 1] Authenticating with CCTV Admin credentials...")
    login_resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "cctv@gmail.com", "password": "123456789"}
    )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("  -> Authentication successful! JWT bearer acquired.")

    # Step 2: Read test file
    assert os.path.exists(TEST_VIDEO_PATH), f"File {TEST_VIDEO_PATH} not found!"
    file_size = os.path.getsize(TEST_VIDEO_PATH)
    file_sha256 = compute_file_sha256(TEST_VIDEO_PATH)
    print(f"\n[INFO] Sample video size: {file_size} bytes, SHA-256: {file_sha256}")

    # Step 3: Chunked upload test (using 25,000 bytes chunk size to produce multiple chunks)
    CHUNK_SIZE = 25000
    total_chunks = math.ceil(file_size / CHUNK_SIZE)
    print(f"\n[TEST 2] Initializing upload session with {total_chunks} chunks ({CHUNK_SIZE} B/chunk)...")
    
    init_payload = {
        "title": "CAM-01 Perimeter Zone Alpha",
        "filename": "sample_surveillance.mp4",
        "file_size": file_size,
        "content_type": "video/mp4",
        "total_chunks": total_chunks,
        "chunk_size": CHUNK_SIZE,
        "description": "Live container automated test stream",
        "expected_sha256": file_sha256
    }
    init_resp = requests.post(f"{BASE_URL}/videos/upload/init", json=init_payload, headers=headers)
    assert init_resp.status_code == 201, f"Init failed: {init_resp.text}"
    init_data = init_resp.json()
    upload_id = init_data["upload_id"]
    video_id = init_data["video_id"]
    print(f"  -> Session created: upload_id={upload_id}, video_id={video_id}")

    # Upload each chunk
    print("\n[TEST 3] Uploading sequential chunks with integrity hashes...")
    with open(TEST_VIDEO_PATH, "rb") as f:
        for idx in range(total_chunks):
            chunk_data = f.read(CHUNK_SIZE)
            chunk_hash = compute_sha256(chunk_data)
            
            files = {"file": ("chunk.part", chunk_data, "application/octet-stream")}
            data = {
                "upload_id": upload_id,
                "chunk_index": idx,
                "chunk_hash": chunk_hash
            }
            chunk_resp = requests.post(f"{BASE_URL}/videos/upload/chunk", data=data, files=files, headers=headers)
            assert chunk_resp.status_code == 200, f"Chunk {idx} failed: {chunk_resp.text}"
            print(f"  -> Chunk {idx + 1}/{total_chunks} ({len(chunk_data)} bytes) uploaded and verified.")

    # Verify session status before completion
    status_resp = requests.get(f"{BASE_URL}/videos/upload/{upload_id}/status", headers=headers)
    assert status_resp.status_code == 200, f"Status check failed: {status_resp.text}"
    status_data = status_resp.json()
    assert len(status_data["uploaded_chunks"]) == total_chunks, "Missing chunks in status!"
    print(f"  -> Upload status confirmed: {len(status_data['uploaded_chunks'])}/{total_chunks} chunks stored.")

    # Step 4: Complete upload session
    print("\n[TEST 4] Finalizing and assembling video in MinIO storage...")
    complete_payload = {
        "upload_id": upload_id,
        "expected_sha256": file_sha256
    }
    complete_resp = requests.post(f"{BASE_URL}/videos/upload/complete", json=complete_payload, headers=headers)
    assert complete_resp.status_code == 200, f"Complete failed: {complete_resp.text}"
    comp_data = complete_resp.json()
    print(f"  -> Video assembled. Status: {comp_data['status']}")

    # Step 5: Poll for FFmpeg metadata processing
    print("\n[TEST 5] Awaiting FFmpeg / FFprobe background processing pipeline...")
    max_retries = 15
    video_details = None
    for attempt in range(max_retries):
        poll_resp = requests.get(f"{BASE_URL}/videos/{video_id}", headers=headers)
        assert poll_resp.status_code == 200, f"Get video failed: {poll_resp.text}"
        video_details = poll_resp.json()
        print(f"  -> [Poll {attempt + 1}/{max_retries}] Status: {video_details['status']}")
        if video_details["status"] == "READY":
            break
        elif video_details["status"] == "FAILED":
            raise RuntimeError(f"Processing failed with error: {video_details.get('error_message')}")
        time.sleep(1.0)

    assert video_details["status"] == "READY", f"Video did not reach READY status! Current: {video_details['status']}"
    print("  -> FFprobe telemetry extracted:")
    print(f"     * Resolution: {video_details['width']}x{video_details['height']}")
    print(f"     * Duration: {video_details['duration_seconds']}s")
    print(f"     * FPS: {video_details['fps']}")
    print(f"     * Video Codec: {video_details['video_codec']}")
    print(f"     * Bitrate: {video_details['bitrate']} bps")
    print(f"     * Thumbnail Key/URL: {video_details['thumbnail_url']}")

    assert video_details["width"] == 1280
    assert video_details["height"] == 720
    assert video_details["video_codec"] == "h264"
    assert video_details["duration_seconds"] is not None and video_details["duration_seconds"] > 3.0

    # Step 6: Verify Thumbnail generation
    print("\n[TEST 6] Verifying surveillance thumbnail image...")
    thumb_resp = requests.get(f"{BASE_URL}/videos/{video_id}/thumbnail", headers=headers)
    assert thumb_resp.status_code == 200, f"Thumbnail failed: {thumb_resp.status_code}"
    assert "image/jpeg" in thumb_resp.headers.get("content-type", ""), f"Unexpected content-type: {thumb_resp.headers.get('content-type')}"
    assert len(thumb_resp.content) > 1000, f"Thumbnail image too small: {len(thumb_resp.content)} bytes"
    print(f"  -> Thumbnail verified! Content-Type: {thumb_resp.headers.get('content-type')}, Size: {len(thumb_resp.content)} bytes")

    # Step 7: HTTP 206 Partial Content Range Streaming
    print("\n[TEST 7] Verifying HTTP 206 Partial Content Range Streaming...")
    range_headers = {**headers, "Range": "bytes=0-1024"}
    stream_resp = requests.get(f"{BASE_URL}/videos/{video_id}/stream", headers=range_headers)
    assert stream_resp.status_code == 206, f"Expected 206 Partial Content, got {stream_resp.status_code}"
    assert stream_resp.headers.get("Accept-Ranges") == "bytes", "Missing Accept-Ranges: bytes"
    content_range = stream_resp.headers.get("Content-Range")
    assert content_range and content_range.startswith("bytes 0-1024/"), f"Unexpected Content-Range: {content_range}"
    assert len(stream_resp.content) == 1025, f"Expected 1025 bytes, got {len(stream_resp.content)}"
    print(f"  -> Range request successful: HTTP 206, Content-Range: {content_range}")

    # Mid-file seek range test
    range_mid = {**headers, "Range": "bytes=10000-20000"}
    stream_mid_resp = requests.get(f"{BASE_URL}/videos/{video_id}/stream", headers=range_mid)
    assert stream_mid_resp.status_code == 206
    assert stream_mid_resp.headers.get("Content-Range").startswith("bytes 10000-20000/")
    assert len(stream_mid_resp.content) == 10001
    print("  -> Mid-stream seek (bytes=10000-20000) verified!")

    # Step 8: Search, Filter, and Pagination
    print("\n[TEST 8] Verifying video library querying and filtering...")
    list_resp = requests.get(f"{BASE_URL}/videos?q=Perimeter&status=READY&page=1&page_size=10", headers=headers)
    assert list_resp.status_code == 200, f"List failed: {list_resp.text}"
    list_data = list_resp.json()
    assert list_data["total"] >= 1
    assert any(v["id"] == str(video_id) for v in list_data["items"])
    print(f"  -> Filter and search verified! Total matching videos: {list_data['total']}")

    # Step 9: Resumable / Interrupted Upload Simulation
    print("\n[TEST 9] Verifying interrupted upload resume workflow...")
    init2_payload = {
        "title": "CAM-02 Gate Entrance Resumable Test",
        "filename": "sample_surveillance.mp4",
        "file_size": file_size,
        "content_type": "video/mp4",
        "total_chunks": 3,
        "chunk_size": CHUNK_SIZE,
        "expected_sha256": file_sha256
    }
    init2_resp = requests.post(f"{BASE_URL}/videos/upload/init", json=init2_payload, headers=headers)
    assert init2_resp.status_code == 201
    init2_data = init2_resp.json()
    u2_id = init2_data["upload_id"]
    v2_id = init2_data["video_id"]

    # Upload only chunk 0 and interrupt
    with open(TEST_VIDEO_PATH, "rb") as f:
        c0 = f.read(CHUNK_SIZE)
        requests.post(
            f"{BASE_URL}/videos/upload/chunk",
            data={"upload_id": u2_id, "chunk_index": 0, "chunk_hash": compute_sha256(c0)},
            files={"file": ("chunk_0.part", c0, "application/octet-stream")},
            headers=headers
        )

    # Inspect status (client re-connects after crash / network interruption)
    s2_resp = requests.get(f"{BASE_URL}/videos/upload/{u2_id}/status", headers=headers)
    assert s2_resp.status_code == 200
    s2_data = s2_resp.json()
    assert s2_data["uploaded_chunks"] == [0], f"Expected [0], got {s2_data['uploaded_chunks']}"
    print(f"  -> Network pause detected: server retained chunk {s2_data['uploaded_chunks']}")

    # Resume: upload chunk 1 and 2
    with open(TEST_VIDEO_PATH, "rb") as f:
        f.seek(CHUNK_SIZE)
        c1 = f.read(CHUNK_SIZE)
        requests.post(
            f"{BASE_URL}/videos/upload/chunk",
            data={"upload_id": u2_id, "chunk_index": 1, "chunk_hash": compute_sha256(c1)},
            files={"file": ("chunk_1.part", c1, "application/octet-stream")},
            headers=headers
        )
        c2 = f.read(CHUNK_SIZE)
        requests.post(
            f"{BASE_URL}/videos/upload/chunk",
            data={"upload_id": u2_id, "chunk_index": 2, "chunk_hash": compute_sha256(c2)},
            files={"file": ("chunk_2.part", c2, "application/octet-stream")},
            headers=headers
        )

    # Finalize resumed session
    c2_complete = requests.post(f"{BASE_URL}/videos/upload/complete", json={"upload_id": u2_id}, headers=headers)
    assert c2_complete.status_code == 200
    print("  -> Interrupted upload resumed and completed cleanly!")

    print("\n==================================================")
    print("  ALL 9 LIVE CONTAINER TESTS PASSED SUCCESSFULLY! ")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
