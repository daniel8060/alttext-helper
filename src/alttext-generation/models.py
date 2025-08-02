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

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import uuid
from datetime import datetime
import enum
from sqlalchemy import Enum as SQLEnum

class JobStatus(enum.Enum):
    PENDING = "pending"
    FAILED = "failed"
    COMPLETED = "completed"

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

    contacts: Mapped[dict[str, str]] = mapped_column(
        JSON,
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default= lambda : datetime.now(datetime.timezone.utc), 
        server_default=func.now()
    )

    jobs: Mapped[list["Job"]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan"
    )

class Job(Base):
    __tablename__ = "job"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customer.id", ondelete="CASCADE"),
        nullable=False
    )

    original_zip_path: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    request_template: Mapped[dict] = mapped_column(
        JSON,
        nullable=False
    )

    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus, name="job_status"),
        default=JobStatus.PENDING,
        server_default="Pending"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(datetime.timezone.utc),
        server_default=func.now()
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    customer: Mapped["Customer"] = relationship(
        back_populates="jobs"
    )

    batches: Mapped[list["Batch"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan"
    )

class Batch(Base):
    __tablename__ = "batch"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("job.id", ondelete="CASCADE"),
        nullable=False
    )

    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    output_file_id: Mapped[str] = mapped_column(
        String,
        default = lambda : None,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(datetime.timezone.utc),
        server_default=func.now()
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        server_default="pending"
    )

    api_response: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )

    job: Mapped["Job"] = relationship(
        back_populates="batches"
    )

    images: Mapped[list["ImageRecord"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan"
    )

    api_calls: Mapped[list["BatchAPICall"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan"
    )