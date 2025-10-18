from sqlmodel import SQLModel, Field, create_engine
from datetime import datetime
from typing import Optional
import uuid

DATABASE_URL = "sqlite:///./human_in_loop.db"
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})


class KBEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    question: str
    answer: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class HelpRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ticket_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    caller: str
    question: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    state: str = Field(default="PENDING")
    supervisor_answer: Optional[str] = None
    resolved_at: Optional[datetime] = None
    room_url: Optional[str] = None  # ✅ new field for LiveKit link


SQLModel.metadata.create_all(engine)
