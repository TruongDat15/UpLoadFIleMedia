import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Cho phép nhận request từ Client (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Định nghĩa 2 thư mục rõ ràng trên ổ đĩa theo đúng thư mục chứa file này
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_files")  # Nơi chứa các file HOÀN THIỆN cuối cùng
CHUNKS_DIR = os.path.join(BASE_DIR, "file_chunks")  # Nơi chứa các MẢNH TẠM THỜI trong quá trình upload

# Tự động tạo thư mục nếu chưa tồn tại
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHUNKS_DIR, exist_ok=True)


# 1. API nhận từng mảnh file (Chunk) và lưu vào thư mục tạm
@app.post("/upload-chunk")
async def upload_chunk(
        file: UploadFile = File(...),
        filename: str = Form(...),
        chunk_index: int = Form(...)
):
    # Tạo một thư mục tạm riêng cho file này dựa theo tên file (ví dụ: ./file_chunks/video.mp4/)
    file_chunks_folder = os.path.join(CHUNKS_DIR, filename)
    os.makedirs(file_chunks_folder, exist_ok=True)

    # Đường dẫn lưu mảnh hiện tại (tên mảnh chính là số thứ tự: 0, 1, 2...)
    chunk_path = os.path.join(file_chunks_folder, str(chunk_index))

    # Ghi mảnh này trực tiếp xuống ổ đĩa
    with open(chunk_path, "wb") as f:
        shutil.copyfileobj(file.file, f)  # type: ignore[arg-type]

    return {"message": f"Chunk {chunk_index} đã lưu vào thư mục tạm thành công"}


# 2. API gộp các mảnh lại và LƯU THẲNG THÀNH FILE HOÀN CHỈNH vào thư mục chính
@app.post("/merge-chunks")
async def merge_chunks(
        filename: str = Form(...),
        total_chunks: int = Form(...)
):
    # Đường dẫn tới thư mục chứa các mảnh tạm
    file_chunks_folder = os.path.join(CHUNKS_DIR, filename)

    # Đường dẫn đích của FILE HOÀN CHỈNH (Lưu thẳng vào thư mục UPLOAD_DIR)
    final_file_path = os.path.join(UPLOAD_DIR, filename)

    # Kiểm tra xem thư mục tạm của file này có tồn tại không
    if not os.path.exists(file_chunks_folder):
        raise HTTPException(status_code=400, detail="Không tìm thấy các mảnh tạm của file này")

    try:
        # Mở một file mới tại thư mục chính thức để chuẩn bị ghi nối các mảnh
        with open(final_file_path, "wb") as final_file:
            # Chạy vòng lặp từ mảnh 0 đến mảnh cuối cùng theo đúng thứ tự
            for i in range(total_chunks):
                chunk_path = os.path.join(file_chunks_folder, str(i))

                # Nếu chẳng may thiếu mất 1 mảnh giữa chừng thì báo lỗi ngay
                if not os.path.exists(chunk_path):
                    raise HTTPException(status_code=400, detail=f"Bị thiếu mảnh số {i}, không thể gộp file")

                # Đọc dữ liệu từ mảnh tạm và GHI NỐI TIẾP vào file hoàn chỉnh
                with open(chunk_path, "rb") as chunk_file:
                    final_file.write(chunk_file.read())

        # Giữ lại các chunk để bạn có thể kiểm tra file đã chia nhỏ trên ổ đĩa.
        # Nếu muốn dọn tự động sau khi merge thì mở dòng dưới ra:
        # shutil.rmtree(file_chunks_folder)

        return {
            "status": "success",
            "message": "Gộp file thành công!",
            "saved_at": final_file_path  # Trả về đường dẫn file đã lưu trên server
        }

    except Exception as e:
        # Nếu có lỗi gì xảy ra trong lúc gộp (ổ đĩa đầy, quyền ghi file...), trả về lỗi 500
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống khi gộp file: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    # Chạy server ở port 8088 như bạn cấu hình
    uvicorn.run(app, host="127.0.0.1", port=8088)