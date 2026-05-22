#!/usr/bin/env python3
"""
Script test để debug vấn đề xem video HLS
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8888"

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_system_info():
    print_header("1. KIỂM TRA HỆ THỐNG")
    try:
        response = requests.get(f"{BASE_URL}/debug/system-info")
        data = response.json()

        print(f"✓ Script dir: {data['script_dir']}")
        print(f"✓ Base dir: {data['base_dir']}")
        print(f"✓ HLS dir: {data['hls_dir']}")
        print(f"  Tồn tại: {'✅' if data['hls_dir_exists'] else '❌'}")
        print(f"✓ Temp dir: {data['temp_dir']}")
        print(f"  Tồn tại: {'✅' if data['temp_dir_exists'] else '❌'}")
        print(f"✓ Final dir: {data['final_dir']}")
        print(f"  Tồn tại: {'✅' if data['final_dir_exists'] else '❌'}")
        print(f"✓ Thumb dir: {data['thumb_dir']}")
        print(f"  Tồn tại: {'✅' if data['thumb_dir_exists'] else '❌'}")

        # Check nếu tất cả directories tồn tại
        all_exist = all([
            data['hls_dir_exists'],
            data['temp_dir_exists'],
            data['final_dir_exists'],
            data['thumb_dir_exists']
        ])

        if not all_exist:
            print("\n⚠️  CẢNH BÁO: Một số thư mục không tồn tại!")
            return False

        return True

    except requests.exceptions.ConnectionError:
        print("❌ LỖI: Không thể kết nối đến server!")
        print(f"   Kiểm tra server đang chạy ở {BASE_URL}")
        return False
    except Exception as e:
        print(f"❌ LỖI: {e}")
        return False


def test_debug_videos():
    print_header("2. KIỂM TRA VIDEOS TRONG DATABASE")
    try:
        response = requests.get(f"{BASE_URL}/debug/videos")
        data = response.json()

        videos = data.get('videos', [])
        total = data.get('total', 0)

        print(f"Tổng số videos: {total}")

        if total == 0:
            print("⚠️  Chưa có video nào!")
            return False

        for i, video in enumerate(videos, 1):
            print(f"\n[Video #{i}]")
            print(f"  • ID: {video['video_id']}")
            print(f"  • Filename: {video['filename']}")
            print(f"  • Status: {video['status']}")
            print(f"  • HLS Path: {video['hls_path']}")
            print(f"    Tồn tại: {'✅' if video['hls_path_exists'] else '❌'}")
            print(f"  • Playlist: {'✅' if video['playlist_exists'] else '❌'}")
            print(f"  • Segments: {video['segment_count']} ✓")
            print(f"  • Duration: {video['duration']}s")
            print(f"  • Created: {video['created_at']}")

            # Kiểm tra video hợp lệ
            is_valid = (
                video['status'] == 'READY' and
                video['hls_path_exists'] and
                video['playlist_exists'] and
                video['segment_count'] > 0
            )

            if not is_valid:
                print(f"  ❌ Video này không hợp lệ!")

        return True

    except Exception as e:
        print(f"❌ LỖI: {e}")
        return False


def test_list_videos():
    print_header("3. DANH SÁCH VIDEOS SẴN XANG XEM")
    try:
        response = requests.get(f"{BASE_URL}/video/list")
        data = response.json()

        videos = data.get('videos', [])
        total = data.get('total', 0)

        print(f"Videos sẵn sàng: {total}")

        if total == 0:
            print("⚠️  Chưa có video nào sẵn sàng để xem!")
            return False

        for i, video in enumerate(videos, 1):
            print(f"\n[Video #{i}]")
            print(f"  • Filename: {video['filename']}")
            print(f"  • Duration: {video['duration']}s")
            print(f"  • Playlist: {BASE_URL}{video['playlist_url']}")
            print(f"  • Thumbnail: {BASE_URL}{video['thumbnail_url']}")

        return True

    except Exception as e:
        print(f"❌ LỖI: {e}")
        return False


def test_video_endpoints(video_id):
    print_header(f"4. KIỂM TRA ENDPOINTS VỚI VIDEO {video_id[:8]}...")

    # Test playlist
    print("\n[TEST Playlist]")
    try:
        response = requests.get(f"{BASE_URL}/video/{video_id}/playlist.m3u8", timeout=5)
        if response.status_code == 200:
            print(f"✅ Playlist endpoint hoạt động")
            # In một vài dòng đầu của playlist
            content = response.text.split('\n')[:5]
            for line in content:
                if line.strip():
                    print(f"   {line}")
        else:
            print(f"❌ Playlist endpoint trả lỗi {response.status_code}")
            print(f"   {response.json()}")
    except Exception as e:
        print(f"❌ Lỗi khi test playlist: {e}")

    # Test info
    print("\n[TEST Info]")
    try:
        response = requests.get(f"{BASE_URL}/video/{video_id}/info", timeout=5)
        if response.status_code == 200:
            print(f"✅ Info endpoint hoạt động")
            info = response.json()
            print(f"   Filename: {info['filename']}")
            print(f"   Duration: {info['duration']}s")
            print(f"   Status: {info['status']}")
        else:
            print(f"❌ Info endpoint trả lỗi {response.status_code}")
    except Exception as e:
        print(f"❌ Lỗi khi test info: {e}")

    # Test thumbnail
    print("\n[TEST Thumbnail]")
    try:
        response = requests.get(f"{BASE_URL}/video/{video_id}/thumbnail", timeout=5)
        if response.status_code == 200:
            print(f"✅ Thumbnail endpoint hoạt động ({len(response.content)} bytes)")
        else:
            print(f"❌ Thumbnail endpoint trả lỗi {response.status_code}")
    except Exception as e:
        print(f"❌ Lỗi khi test thumbnail: {e}")


def main():
    print("\n")
    print(" " * 20 + "[*] TEST HLS VIDEO STREAMING")
    print(" " * 20 + "=" * 30)

    # Test 1: System info
    if not test_system_info():
        print("\n❌ Hệ thống không được cấu hình đúng!")
        sys.exit(1)

    # Test 2: Debug videos
    if not test_debug_videos():
        print("\n⚠️  Không có videos trong database!")
        print("   Hãy upload một video trước!")
        sys.exit(1)

    # Test 3: List videos
    if not test_list_videos():
        print("\n⚠️  Không có videos sẵn sàng!")
        print("   Video có thể đang trong quá trình convert HLS")
        sys.exit(1)

    # Test 4: Endpoints
    response = requests.get(f"{BASE_URL}/video/list")
    videos = response.json().get('videos', [])
    if videos:
        first_video_id = videos[0]['video_id']
        test_video_endpoints(first_video_id)

    print_header("✅ TEST HOÀN THÀNH")
    print("""
Nếu tất cả đều ✅, video của bạn sẵn sàng xem!

Nếu có ❌:
1. Kiểm tra logs server (dòng [DEBUG], [ERROR])
2. Chạy: curl {}/debug/videos
3. Kiểm tra filesystem thủ công
4. Xem FIX_404_ERROR.md để biết thêm chi tiết
    """.format(BASE_URL))


if __name__ == "__main__":
    main()

