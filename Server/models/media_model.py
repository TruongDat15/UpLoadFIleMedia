from enum import Enum
from enum import IntEnum

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import BigInteger
from sqlalchemy import ForeignKey
from sqlalchemy import DateTime

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from core.database import Base


class FileType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"


class Status(IntEnum):
    PENDING = 0
    CONVERTING = 1
    COMPLETE = 2
    FAIL = 3


class Media(Base):
    __tablename__ = "media"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    title = Column(
        String(255),
        nullable=False
    )

    file_type = Column(
        String(20),
        nullable=False
    )

    original_path = Column(
        String(500),
        nullable=False
    )

    thumb_path = Column(
        String(500),
        nullable=True
    )

    file_size = Column(
        BigInteger,
        nullable=False
    )

    status = Column(
        Integer,
        nullable=False,
        default=Status.PENDING.value,
        server_default="0"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    user = relationship(
        "User",
        back_populates="medias"
    )