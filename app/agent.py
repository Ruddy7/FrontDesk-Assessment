import asyncio
from typing import Optional
from .db import engine, KBEntry, HelpRequest
from .notifications import notify_supervisor
from sqlmodel import Session, select

from livekit import api
from dotenv import load_dotenv
import os
from pathlib import Path

# --- Load environment variables ---
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
LIVEKIT_URL = os.getenv("LIVEKIT_URL")

if not all([LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_URL]):
    raise ValueError("LiveKit environment variables not set properly")

lkapi = api.LiveKitAPI(
    url=LIVEKIT_URL,
    api_key=LIVEKIT_API_KEY,
    api_secret=LIVEKIT_API_SECRET
)

room_service = lkapi.room


# --- LiveKit room creation ---
async def create_livekit_room(room_name: str) -> str:
    """Creates a LiveKit room and returns the URL."""
    options = api.RoomCreateOptions(name=room_name, empty_timeout=600)
    room = await room_service.create_room(options)
    room_url = f"{LIVEKIT_URL}/room/{room.name}"
    return room_url


# --- KB lookup ---
def find_in_kb(question: str) -> Optional[KBEntry]:
    with Session(engine) as session:
        stmt = select(KBEntry)
        for r in session.exec(stmt):
            if r.question.strip().lower() in question.lower():
                return r
    return None


# --- Create help request ---
def create_help_request(caller: str, question: str) -> HelpRequest:
    hr = HelpRequest(caller=caller, question=question)
    with Session(engine) as session:
        session.add(hr)
        session.commit()
        session.refresh(hr)

    notify_supervisor(hr)

    # 🔥 Create LiveKit room asynchronously
    asyncio.create_task(spawn_room_for_ticket(hr.ticket_id))
    return hr


async def spawn_room_for_ticket(ticket_id: str):
    """Helper coroutine to create and store LiveKit room URL."""
    room_url = await create_livekit_room(f"support-{ticket_id}")
    with Session(engine) as session:
        hr = session.exec(select(HelpRequest).where(HelpRequest.ticket_id == ticket_id)).first()
        if hr:
            hr.room_url = room_url
            session.add(hr)
            session.commit()
