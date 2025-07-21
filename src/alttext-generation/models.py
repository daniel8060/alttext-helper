from sqlalchemy import (
    ForeignKey,
    String,
    Text,
    JSON,
    DateTime,
    Integer,
    Boolean,
    LargeBinary,
)

from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import uuid
from datetime import datetime

class Base(DeclarativeBase):
    pass 

class Customer(Base):
    __tablename__ = "customer"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    organization_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    emails: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default= datetime.now(datetime.timezone.utc), 
        server_default=func.now()
    )

    jobs: Mapped[list["Job"]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan"
    )