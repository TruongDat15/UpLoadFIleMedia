import os
import requests

CHUNK_SIZE = 1024 * 1024  # 1 MB mỗi chunk
FILE_TO_UPLOAD = "336149.mp4"  # Hãy đổi tên thành file thực tế bạn đang có ở máy
SERVER_URL = "http://127.0.0.1:8088"


def upload_large_file(file_path):
    filename = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    # Tính toán tổng số chunk cần gửi
    total_chunks = (file_size // CHUNK_SIZE) + (1 if file_size % CHUNK_SIZE > 0 else 0)
    print(f"Bắt đầu upload {filename} ({file_size} bytes) chia thành {total_chunks} chunks...")

    with open(file_path, "rb") as f:
        for chunk_index in range(total_chunks):
            # Đọc đúng 1MB dữ liệu từ file
            chunk_data = f.read(CHUNK_SIZE)

            # Gửi chunk này lên server kèm thông tin định danh
            files = {"file": (f"chunk_{chunk_index}", chunk_data)}
            data = {"filename": filename, "chunk_index": chunk_index}

            response = requests.post(f"{SERVER_URL}/upload-chunk", files=files, data=data)

            if response.status_code == 200:
                print(f"-> Đã gửi thành công chunk {chunk_index + 1}/{total_chunks}")
            else:
                print(f"X Lỗi khi gửi chunk {chunk_index}: {response.text}")
                return

    # Sau khi gửi hết tất cả các chunk, gửi lệnh yêu cầu Backend gộp file lại
    print("Tất cả chunk đã lên server. Đang yêu cầu gộp file...")
    merge_data = {"filename": filename, "total_chunks": total_chunks}
    merge_response = requests.post(f"{SERVER_URL}/merge-chunks", data=merge_data)

    print(merge_response.json().get("message"))


if __name__ == "__main__":
    # Tạo nhanh một file giả lập khoảng 3.5MB nếu bạn chưa có file sẵn để test
    if not os.path.exists(FILE_TO_UPLOAD):

        print("Khong có thấy video nào ")
        with open(FILE_TO_UPLOAD, "wb") as f:
            f.write(os.urandom(35 * 1024 * 1024 // 10))  # ~3.5MB dữ liệu ngẫu nhiên

    upload_large_file(FILE_TO_UPLOAD)