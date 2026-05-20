from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from api.common import save_upload_file, status_label
from api.deps import get_db
from models.media_model import FileType, Media, Status
from models.user_model import User

router = APIRouter(prefix="/upload-image", tags=["upload-image"])


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
def upload_image(
    user_id: int = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    print("[upload_image] start")
    print(f"[upload_image] user_id={user_id}, title={title}, filename={file.filename}, content_type={file.content_type}")

    user = db.get(User, user_id)
    if not user:
        print(f"[upload_image] user not found: user_id={user_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not (file.content_type or "").startswith("image/"):
        print(f"[upload_image] invalid file type: {file.content_type}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be an image")

    print("[upload_image] saving file to disk...")
    saved_path = save_upload_file(file, "images")
    file_size = saved_path.stat().st_size
    print(f"[upload_image] file saved: {saved_path} ({file_size} bytes)")

    media = Media(
        user_id=user_id,
        title=title,
        file_type=FileType.IMAGE.value,
        original_path=str(saved_path),
        thumb_path="",
        file_size=file_size,
        status=Status.COMPLETE.value,
    )
    print("[upload_image] inserting media record...")
    db.add(media)
    db.commit()
    db.refresh(media)
    print(f"[upload_image] done: media_id={media.id}, status={media.status}")
    return _build_media_response(media)

@router.post("/convetingMedia")
def conveting_media(
    user_id: int = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    print("[conveting_media] start")
    print(f"[conveting_media] user_id={user_id}, title={title}, filename={file.filename}, content_type={file.content_type}")

    if not (file.content_type or "").startswith("image/"):
        print(f"[conveting_media] invalid file type: {file.content_type}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be an image")

    mediaIn = Media(
        user_id=user_id,
        title=title,
        file_type=FileType.IMAGE.value,

        status=Status.CONVERTING.value,
    )

    print("[conveting_media] inserting media record with CONVERTING status...")
    db.add(mediaIn)
    db.commit()
    db.refresh(mediaIn)

    print(f"[conveting_media] done: media_id={mediaIn.id}, status={mediaIn.status}")

    return _build_media_response(mediaIn)
