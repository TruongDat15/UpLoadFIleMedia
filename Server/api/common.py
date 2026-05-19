from __future__ import annotations

from pathlib import Path
from shutil import copyfileobj
from uuid import uuid4

from fastapi import UploadFile

from core.settings import PROJECT_ROOT
from models.media_model import Status

UPLOAD_ROOT = PROJECT_ROOT / "data" / "upload"


def ensure_upload_dir(folder_name: str) -> Path:
    target_dir = UPLOAD_ROOT / folder_name
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


def save_upload_file(upload_file: UploadFile, folder_name: str) -> Path:
    target_dir = ensure_upload_dir(folder_name)
    original_name = Path(upload_file.filename or "file").name
    safe_name = f"{uuid4().hex}_{original_name}"
    destination = target_dir / safe_name

    with destination.open("wb") as buffer:
        copyfileobj(upload_file.file, buffer)

    return destination


def status_label(status_value: int) -> str:
    try:
        return Status(status_value).name.lower()
    except ValueError:
        return str(status_value)

