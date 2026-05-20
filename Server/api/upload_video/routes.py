from __future__ import annotations

import json
import math
import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from api.common import save_upload_file, status_label
from api.deps import get_db
from core.settings import get_settings
from models.media_model import FileType, Media, Status
from models.user_model import User
from service.s3_service import S3Client

router = APIRouter(prefix="/upload-video", tags=["upload-video"])

settings = get_settings()


def _build_media_response(media: Media) -> dict:
    return {
        "id": media.id,
        "user_id": media.user_id,
        "title": media.title,
        "file_type": media.file_type,
        "original_path": media.original_path,
        "thumb_path": media.thumb_path,
        "file_size": media.file_size,
        "status": status_label(media.status),
        "created_at": media.created_at,
    }


@router.post("")
def upload_video(
    user_id: int = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not (file.content_type or "").startswith("video/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a video")

    saved_path = save_upload_file(file, "videos")
    file_size = saved_path.stat().st_size

    media = Media(
        user_id=user_id,
        title=title,
        file_type=FileType.VIDEO.value,
        original_path=str(saved_path),
        thumb_path="",
        file_size=file_size,
        status=Status.PENDING.value,
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return _build_media_response(media)


@router.post("/init")
async def init_upload(filename: str = Form(...), file_size: int = Form(...)):
    try:
        # Gọi MinIO mở cuộc Multipart Upload

        s3_client = S3Client()
        response = s3_client.create_multipart_upload(Bucket=settings.bucket, Key=filename)
        upload_id = response['UploadId']

        total_chunks = math.ceil(file_size / settings.chunk_size)
        presigned_urls = []

        for i in range(1, total_chunks + 1):
            # MinIO sẽ tự sinh link PUT hướng trực tiếp về IP/Port của MinIO
            url = s3_client.generate_presigned_url(
                ClientMethod='upload_part',
                Params={
                    'Bucket': settings.bucket,
                    'Key': filename,
                    'UploadId': upload_id,
                    'PartNumber': i
                },
                ExpiresIn=900
            )
            presigned_urls.append({"part_number": i, "url": url})

        return {"upload_id": upload_id, "presigned_urls": presigned_urls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- API 2: CHỐT ĐƠN & BÁO HOÀN THÀNH ĐỂ CẬP NHẬT TRẠNG THÁI PENDING ---
@router.post("/complete")
async def complete_upload(filename: str = Form(...),
                          upload_id: str = Form(...),
                          parts_data: str = Form(...),
                          file_size: int = Form(...),
                          user_id: int = Form(...),
                          db: Session = Depends(get_db)
                          ):
    try:
        s3_client = S3Client()
        parts = json.loads(parts_data)
        s3_parts = [{'PartNumber': p['part_number'], 'ETag': p['etag']} for p in parts]

        # Ra lệnh cho MinIO gộp các mảnh lại ngay trên server MinIO
        s3_client.complete_multipart_upload(
            Bucket=settings.bucket,
            Key=filename,
            UploadId=upload_id,
            MultipartUpload={'Parts': s3_parts}
        )

        # ĐƯỜNG DẪN FILE THẬT TRÊN MINIO ĐỂ SAU NÀY CRONJOB DÙNG
        file_url_on_minio = f"{s3_client.endpoint_url}/{settings.bucket}/{filename}"

        file_type = os.path.splitext(filename)[1].replace(".", "")

        new_media = Media(
            user_id=user_id,
            title=filename,
            file_type=FileType.VIDEO.value,
            original_path=file_url_on_minio,
            thumb_path="",  # Cronjob sẽ cập nhật cái này sau
            file_size=file_size,
            status=Status.PENDING.value  # Gán cứng giá trị = 1 (Pending)
        )

        db.add(new_media)
        db.commit()  # Lưu thực tế xuống file DB
        db.refresh(new_media)

        # LƯU DATABASE: status = 1 (PENDING) kèm file_url_on_minio
        # code_save_db(original_path=file_url_on_minio, status=1)

        print(f"🎉 File {filename} đã gộp xong trên MinIO tại: {file_url_on_minio}")
        return {"status": "success",
                "message": "File uploaded and merged on MinIO!",
                "media_id": new_media.id,
                "db_status": new_media.status
                }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))