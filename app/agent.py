from typing import Optional
from .db import engine, KBEntry, HelpRequest
from .notifications import notify_supervisor, notify_caller_followup
from sqlmodel import Session, select


from livekit import api
from dotenv import load_dotenv
import os
from pathlib import Path

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


async def create_livekit_room(room_name: str):
    options = api.RoomCreateOptions(name=room_name, empty_timeout=30)
    room = await room_service.create_room(options)
    return room


# KB lookup


def find_in_kb(question: str) -> Optional[KBEntry]:
    with Session(engine) as session:
        stmt = select(KBEntry)
        for r in session.exec(stmt):
            if r.question.strip().lower() in question.lower():
                    return r
    return None


# Create help request


def create_help_request(caller: str, question: str) -> HelpRequest:
    hr = HelpRequest(caller=caller, question=question)
    with Session(engine) as session:
        session.add(hr)
        session.commit()
        session.refresh(hr)
    notify_supervisor(hr)
    return hr