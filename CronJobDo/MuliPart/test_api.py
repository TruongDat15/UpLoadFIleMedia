#!/usr/bin/env python3
"""
Test script cho các API endpoints
Run: python test_api.py
"""

import requests
import json
from pathlib import Path

API_BASE = "http://127.0.0.1:8888"

def test_video_list():
    """Test: GET /video/list"""
    print("\n[TEST] GET /video/list")
    try:
        res = requests.get(f"{API_BASE}/video/list", timeout=5)
        print(f"Status: {res.status_code}")
        data = res.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_server_alive():
    """Test: Kiểm tra server sống"""
    print("\n[TEST] Server connection")
    try:
        res = requests.get(f"{API_BASE}/video/list", timeout=2)
        print(f"✓ Server alive (status: {res.status_code})")
        return True
    except Exception as e:
        print(f"✗ Server not responding: {e}")
        return False

def main():
    print("=" * 60)
    print("VIDEO UPLOAD & HLS STREAMING - API TEST")
    print("=" * 60)

    # Test server
    if not test_server_alive():
        print("\nERROR: Server không chạy!")
        print("Hãy chạy server trước:")
        print("  cd D:\\test_gemini\\upLoadFileChunk\\CronJobDo\\MuliPart")
        print("  python -m uvicorn UploadMultiPart:app --reload --port 8888")
        return

    # Test endpoints
    print("\n[INFO] Kiểm tra các endpoints...")

    # 1. List videos
    test_video_list()

    # 2. Upload init (demo)
    print("\n[TEST] POST /upload/init (demo)")
    try:
        res = requests.post(
            f"{API_BASE}/upload/init",
            data={
                "filename": "test_video.mp4",
                "file_size": 1000000,
                "content_type": "video/mp4"
            },
            timeout=5
        )
        print(f"Status: {res.status_code}")
        if res.ok:
            data = res.json()
            print(f"Upload ID: {data['upload_id']}")
            print(f"Chunk size: {data['chunk_size']:,} bytes")
            print(f"Total parts: {data['total_parts']}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 60)
    print("TEST SELESAI!")
    print("=" * 60)
    print("\nGUI: http://127.0.0.1:8888/")
    print("  atau buka: Client.html")

if __name__ == "__main__":
    main()

