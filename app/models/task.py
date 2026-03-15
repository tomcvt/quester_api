import enum, datetime, uuid
from datetime import datetime
from unittest.mock import Base
from sqlalchemy import ForeignKey, String, Enum, Uuid, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.models.base import Base

class TaskType(enum.Enum):
    JOB = "JOB"

class TaskStatus(enum.Enum):
    STARTED = "STARTED"
    ACCEPTED = "ACCEPTED"
    FINISHED = "FINISHED"
    DELETED = "DELETED"
    TIMED_OUT = "TIMED_OUT"

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    public_id: Mapped[uuid.UUID] = mapped_column(Uuid, default=uuid.uuid4, unique=True, nullable=False)
    type: Mapped[TaskType] = mapped_column(Enum(TaskType), nullable=False)
    inclusive: Mapped[bool] = mapped_column(bool, nullable=False)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)





###
#and task which is id, publicId, type enum [JOB] (for now), 
# inclusive boolean (if creator is participating), 
# status [STARTED, ACCEPTED, FINISHED, DELETED, TIMED OUT], 
# created_at, updated_at, creator (userId). 
# as we go we just focus on ONE route for now and i will 
# try to by learning create others and will ask for help in 
# integrating them in services