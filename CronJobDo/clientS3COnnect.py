import os
import requests
import json

FILE_PATH = "video3.mp4"  # File video thực tế trên máy bạn
BE_URL = "http://127.0.0.1:8000"
CHUNK_SIZE = 5 * 1024 * 1024  # 5MB
USER_ID = 1


def upload_file_straight_to_s3(file_path):
    filename = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    # --- BƯỚC 1: Gọi BE xin khởi tạo và lấy danh sách URL ---
    print("[FE] 1. Xin BE cấp phép upload...")
    init_res = requests.post(f"{BE_URL}/api/v1/upload-video/init", data={"filename": filename, "file_size": file_size})
    if not init_res.ok:
        print(f"[FE][ERROR] init failed: status={init_res.status_code}, body={init_res.text}")
        return
    init_data = init_res.json()

    upload_id = init_data["upload_id"]
    urls_list = init_data["presigned_urls"]

    # Nơi lưu lại các biên lai (ETag) sau khi up thành công từng mảnh
    etags_receipts = []

    # --- BƯỚC 2: Cắt file và đẩy THẲNG lên Amazon S3 ---
    print(f"[FE] 2. Bắt đầu đẩy thẳng các chunk lên S3 (Gồm {len(urls_list)} mảnh)...")
    with open(file_path, "rb") as f:
        for item in urls_list:
            part_number = item["part_number"]
            s3_url = item["url"]

            # Đọc đúng 5MB dữ liệu của chunk hiện tại
            chunk_data = f.read(CHUNK_SIZE)

            # Dùng lệnh PUT đẩy THẲNG lên link S3 của Amazon (Không qua BE nữa)
            s3_response = requests.put(s3_url, data=chunk_data)
            if not s3_response.ok:
                print(f"[FE][ERROR] upload part failed: part={part_number}, status={s3_response.status_code}, body={s3_response.text}")
                return

            # Lấy chiếc "biên lai" ETag từ Header do Amazon trả về
            etag = s3_response.headers.get("ETag")

            print(f"   -> Đã up xong mảnh {part_number} lên S3. Nhận ETag: {etag}")
            etags_receipts.append({"part_number": part_number, "etag": etag})

    # --- BƯỚC 3: Báo cáo với BE là em đã up xong hết để BE ra lệnh gộp ---
    print("[FE] 3. Đã up hết lên S3. Gửi danh sách ETag về báo BE chốt đơn...")
    complete_data = {
        "filename": filename,
        "upload_id": upload_id,
        "parts_data": json.dumps(etags_receipts),  # Ép danh sách sang chuỗi JSON
        "file_size": file_size,
        "user_id": USER_ID,
    }

    final_res = requests.post(f"{BE_URL}/api/v1/upload-video/complete", data=complete_data)
    try:
        final_json = final_res.json()
    except Exception:
        print(f"[FE][ERROR] complete response is not JSON: status={final_res.status_code}, body={final_res.text}")
        return

    if final_res.ok:
        print(f"[Result từ BE]: {final_json.get('message', final_json)}")
    else:
        print(f"[FE][ERROR] complete failed: status={final_res.status_code}, body={final_json}")


if __name__ == "__main__":
    # Tạo nhanh file test 12MB (tương đương khoảng 3 chunk) nếu chưa có sẵn file
    if not os.path.exists(FILE_PATH):
        with open(FILE_PATH, "wb") as f:
            f.write(os.urandom(12 * 1024 * 1024))

    upload_file_straight_to_s3(FILE_PATH)