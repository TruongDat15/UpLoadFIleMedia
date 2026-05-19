from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String(100),
        nullable=False,
        unique=True
    )

    email = Column(
        String(255),
        nullable=False,
        unique=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    medias = relationship(
        "Media",
        back_populates="user",
        cascade="all, delete"
    )