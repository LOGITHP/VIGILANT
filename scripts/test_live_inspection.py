"""
Live integration test for Milestone 3.1.1 - FFprobe Metadata Extractor & Media Inspection
Runs against the live Docker stack on http://localhost:8000
"""
import time
import requests

API_BASE = "http://localhost:8000/api/v1"

def run_test():
    print("==================================================================")
    print("   VIGILANT - Live FFprobe Metadata Inspection Integration Test   ")
    print("==================================================================")

    # 1. Authenticate
    print("\n[STEP 1] Authenticating with CCTV administrator account...")
    login_resp = requests.post(f"{API_BASE}/auth/login", json={
        "username": "cctv@gmail.com",
        "password": "123456789"
    })
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[OK] Successfully authenticated! JWT Bearer token acquired.")

    # 2. Record a live surveillance stream clip
    print("\n[STEP 2] Triggering 3-second live surveillance recording on CAM-01...")
    rec_resp = requests.post(
        f"{API_BASE}/videos/live/record",
        json={"camera_id": "CAM-01", "duration_seconds": 3, "description": "Milestone 3.1.1 test stream"},
        headers=headers
    )
    assert rec_resp.status_code == 201, f"Recording failed: {rec_resp.text}"
    video_data = rec_resp.json()
    video_id = video_data["id"]
    print(f"[OK] Recorded live video: ID={video_id}, Title='{video_data['title']}'")

    # 3. Wait for background processing (FFprobe inspection)
    print("\n[STEP 3] Waiting for post-upload FFprobe inspection pipeline...")
    max_wait = 20
    inspection_data = None
    for i in range(max_wait):
        time.sleep(1)
        resp = requests.get(f"{API_BASE}/videos/{video_id}/inspection", headers=headers)
        if resp.status_code == 200:
            inspection_data = resp.json()
            break
        print(f"  ... waiting for inspection completion ({i+1}/{max_wait}s, status: {resp.status_code})")

    assert inspection_data is not None, "Timed out waiting for inspection report!"
    print("[OK] Inspection report successfully generated and retrieved!")

    # 4. Verify 5 metadata categories
    print("\n[STEP 4] Validating 5-Category Telemetry Dissection:")

    # Category A: File Info
    file_info = inspection_data.get("file_info", {})
    print(f"  [Category A: File Info]")
    print(f"    - Original Filename: {file_info.get('original_filename')}")
    print(f"    - File Size:         {file_info.get('file_size')} bytes")
    print(f"    - File Format:       {file_info.get('file_format')}")
    print(f"    - SHA-256 Checksum:  {file_info.get('sha256_checksum')[:24]}...")
    assert file_info.get("file_size") > 0, "Invalid file size"
    assert file_info.get("sha256_checksum"), "Missing SHA-256 checksum"

    # Category B: Container Info
    container_info = inspection_data.get("container_info", {})
    print(f"  [Category B: Container Info]")
    print(f"    - Container Format:  {container_info.get('format_name')}")
    print(f"    - Duration:          {container_info.get('duration_seconds')}s")
    print(f"    - Container Bitrate: {container_info.get('bitrate')} bps")
    assert container_info.get("duration_seconds") > 0, "Invalid container duration"

    # Category C: Video Stream Info
    v_stream = inspection_data.get("video_stream", {})
    print(f"  [Category C: Video Stream Info]")
    print(f"    - Primary Stream:    Index #{v_stream.get('stream_index')}")
    print(f"    - Video Codec:       {v_stream.get('codec_name')} ({v_stream.get('codec_long_name')})")
    print(f"    - Resolution:        {v_stream.get('width')}x{v_stream.get('height')}")
    print(f"    - Reported FPS:      {v_stream.get('fps')} ({v_stream.get('rational_fps')})")
    print(f"    - Pixel Format:      {v_stream.get('pixel_format')}")
    print(f"    - Time Base:         {v_stream.get('time_base')}")
    assert v_stream.get("codec_name") is not None, "Missing video codec"
    assert v_stream.get("width") > 0 and v_stream.get("height") > 0, "Invalid video resolution"

    # Category D: Audio Stream Info
    a_stream = inspection_data.get("audio_stream", {})
    print(f"  [Category D: Audio Stream Info]")
    print(f"    - Has Audio:         {a_stream.get('has_audio')}")
    print(f"    - Audio Codec:       {a_stream.get('codec_name')}")
    print(f"    - Sample Rate:       {a_stream.get('sample_rate')} Hz")
    print(f"    - Channels:          {a_stream.get('channels')}")

    # Category E: Stream Catalog
    streams = inspection_data.get("all_streams", [])
    print(f"  [Category E: Stream Catalog]")
    print(f"    - Total Streams:     {len(streams)}")
    for s in streams:
        pic_flag = " [ATTACHED PIC]" if s.get("is_attached_pic") else ""
        prim_flag = " [PRIMARY]" if s.get("is_primary") else ""
        print(f"      - Stream #{s.get('stream_index')}: {s.get('stream_type')} / {s.get('codec_name')}{prim_flag}{pic_flag}")
    assert len(streams) >= 1, "Expected at least 1 stream in catalog"

    # 5. Verify Dual State Machine Requirement
    print("\n[STEP 5] Verifying State Segregation (metadata_status vs validation_status):")
    print(f"    - metadata_status:   {inspection_data.get('metadata_status')} (Expected: COMPLETED)")
    print(f"    - validation_status: {inspection_data.get('validation_status')} (Expected: PENDING)")
    assert inspection_data.get("metadata_status") == "COMPLETED"
    assert inspection_data.get("validation_status") == "PENDING"
    print("[OK] State segregation verified: metadata successfully extracted while full validation remains PENDING (Milestone 3.1.2).")

    # 6. Test on-demand re-probe trigger endpoint
    print("\n[STEP 6] Testing on-demand re-probe trigger POST /videos/{id}/inspect...")
    reprobe_resp = requests.post(f"{API_BASE}/videos/{video_id}/inspect", headers=headers)
    assert reprobe_resp.status_code == 202, f"Re-probe failed: {reprobe_resp.text}"
    reprobe_body = reprobe_resp.json()
    print(f"[OK] Re-probe queued: {reprobe_body['message']} (status: {reprobe_body['status']})")

    print("\n==================================================================")
    print("   ALL INTEGRATION CHECKS PASSED FOR MILESTONE 3.1.1 DELIVERABLE  ")
    print("==================================================================")

if __name__ == "__main__":
    run_test()
