from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.common import status_label
from api.deps import get_db
from models.media_model import Media

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/medias")
def list_media_history(
    user_id: int | None = None,
    file_type: str | None = None,
    db: Session = Depends(get_db),
):
    query = select(Media).order_by(Media.id.desc())

    if user_id is not None:
        query = query.where(Media.user_id == user_id)
    if file_type is not None:
        query = query.where(Media.file_type == file_type)

    medias = db.execute(query).scalars().all()
    return [
        {
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
        for media in medias
    ]

