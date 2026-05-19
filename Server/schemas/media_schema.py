from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MediaCreate(BaseModel):
    user_id: int
    title: str
    file_type: str
    original_path: str
    thumb_path: Optional[str] = None
    file_size: int


class MediaResponse(BaseModel):
    id: int
    user_id: int
    title: str
    file_type: str
    original_path: str
    thumb_path: Optional[str]
    file_size: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True