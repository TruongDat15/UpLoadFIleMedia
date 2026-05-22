#!/usr/bin/env python3
"""
Upload video test qua API
"""
import math
import requests
from pathlib import Path

BASE_URL = "http://localhost:8888"
CHUNK_SIZE = 5 * 1024 * 1024  # 5MB

def upload_video(video_path: str):
    """Upload video qua API"""
    video_path = Path(video_path)

    if not video_path.exists():
        print(f"❌ Video không tồn tại: {video_path}")
        return

    file_size = video_path.stat().st_size
    total_parts = math.ceil(file_size / CHUNK_SIZE)

    print(f"📹 Video: {video_path.name}")
    print(f"   Size: {file_size / 1024 / 1024:.1f} MB")
    print(f"   Chunks: {total_parts}")

    # 1. Init upload
    print("\n[1/3] Init upload...")
    response = requests.post(
        f"{BASE_URL}/upload/init",
        data={
            'filename': video_path.name,
            'file_size': file_size,
            'content_type': 'video/mp4'
        }
    )

    if response.status_code != 200:
        print(f"❌ Init failed: {response.json()}")
        return

    result = response.json()
    upload_id = result['upload_id']
    print(f"✅ Upload ID: {upload_id}")

    # 2. Upload chunks
    print("\n[2/3] Uploading chunks...")
    with open(video_path, 'rb') as f:
        for part_number in range(1, total_parts + 1):
            chunk_data = f.read(CHUNK_SIZE)

            files = {'chunk': chunk_data}
            response = requests.post(
                f"{BASE_URL}/upload/{upload_id}/chunk/{part_number}",
                files=files
            )

            if response.status_code != 200:
                print(f"❌ Chunk {part_number} failed: {response.json()}")
                return

            percent = (part_number / total_parts) * 100
            print(f"  [{part_number}/{total_parts}] {percent:.0f}%")

    print("✅ All chunks uploaded!")

    # 3. Complete upload
    print("\n[3/3] Completing upload...")
    response = requests.post(f"{BASE_URL}/upload/{upload_id}/complete")

    if response.status_code != 200:
        print(f"❌ Complete failed: {response.json()}")
        return

    result = response.json()
    print(f"✅ Upload completed!")
    print(f"   Final path: {result['final_path']}")

    # 4. Convert to HLS
    print("\n[4/4] Converting to HLS...")
    response = requests.post(f"{BASE_URL}/video/{upload_id}/convert-hls")

    if response.status_code != 200:
        print(f"❌ HLS conversion failed: {response.json()}")
        return

    result = response.json()
    video_id = result['video_id']
    duration = result['duration']
    status = result['status']

    print(f"✅ HLS Conversion complete!")
    print(f"   Video ID: {video_id}")
    print(f"   Duration: {duration}s")
    print(f"   Status: {status}")
    print(f"   Playlist URL: {BASE_URL}/video/{video_id}/playlist.m3u8")

    return video_id

if __name__ == "__main__":
    print("=" * 60)
    print("  UPLOAD VIDEO TEST")
    print("=" * 60)

    # Upload video nhỏ (test nhanh)
    video_file = "D:\\test_gemini\\upLoadFileChunk\\CronJobDo\\336149.mp4"

    print(f"\nUploading: {video_file}\n")
    video_id = upload_video(video_file)

    if video_id:
        print("\n✅ VIDEO UPLOAD THÀNH CÔNG!")
        print("   Bây giờ chạy: python test_video_streaming.py")
    else:
        print("\n❌ UPLOAD THẤT BẠI!")

