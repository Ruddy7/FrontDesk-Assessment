"""
Database models and configuration for the salon helpdesk system.
"""
from sqlmodel import SQLModel, Field, create_engine
from datetime import datetime
from typing import Optional
import uuid

DATABASE_URL = "sqlite:///./human_in_loop.db"
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    connect_args={"check_same_thread": False}
)


class KBEntry(SQLModel, table=True):
    """Knowledge Base entry for frequently asked questions."""
    id: Optional[int] = Field(default=None, primary_key=True)
    question: str = Field(index=True)  # Index for faster lookups
    answer: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    def __repr__(self):
        return f"<KBEntry(id={self.id}, question='{self.question[:30]}...')>"


class HelpRequest(SQLModel, table=True):
    """Help request from a caller requiring supervisor assistance."""
    id: Optional[int] = Field(default=None, primary_key=True)
    ticket_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        unique=True,
        index=True  # Index for faster lookups
    )
    caller: str
    question: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    state: str = Field(default="PENDING", index=True)  # PENDING, RESOLVED, UNRESOLVED
    supervisor_answer: Optional[str] = None
    resolved_at: Optional[datetime] = None
    room_url: Optional[str] = None  # LiveKit room name for voice calls

    def __repr__(self):
        return f"<HelpRequest(ticket_id='{self.ticket_id}', caller='{self.caller}', state='{self.state}')>"


# Create all tables
SQLModel.metadata.create_all(engine)
print("[DB] ✓ Database initialized and tables created")