import os
import asyncio
from pathlib import Path
from typing import Optional
from sqlmodel import Session, select
from dotenv import load_dotenv
from livekit import api
from livekit.api import AccessToken, VideoGrants
import json
from .db import engine, HelpRequest, KBEntry
from .notifications import notify_supervisor

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


# --- LiveKit room creation ---
async def create_livekit_room(room_name: str) -> str:
    """
    Creates a LiveKit room and returns the room name (URL-friendly).
    This is idempotent: if the room exists, LiveKit will continue without error.
    """
    try:
        # Use CreateRoomRequest instead of RoomCreateOptions
        room = await lkapi.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                empty_timeout=600,
            )
        )
        created_name = room.name
        print(f"[LiveKit] Room created: {created_name}")
    except Exception as exc:
        # Room might already exist
        print(f"[LiveKit] create_room warning: {exc}")
        created_name = room_name

    return created_name


# --- Generate access token ---
def generate_access_token(identity: str, room_name: str, role: str = "caller") -> str:
    """
    Generate a LiveKit join token (JWT) for a participant identity and room.
    Tested with livekit==1.0.17
    """
    token = AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    token.identity = identity
    token.name = f"{role}_{identity}"
    token.metadata = json.dumps({"role": role})
    
    # IMPORTANT: For livekit 1.0.17, use video_grant (singular), not grants
    token.video_grant = VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True
    )

    jwt_token = token.to_jwt()
    print(f"[TOKEN] Generated for identity={identity}, room={room_name}, length={len(jwt_token)}")
    return jwt_token


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

    # Spawn a task to create the LiveKit room (non-blocking)
    asyncio.create_task(spawn_room_for_ticket(hr.ticket_id))
    return hr


# --- Spawn room for ticket ---
async def spawn_room_for_ticket(ticket_id: str):
    """Helper coroutine to create and store LiveKit room name into the DB."""
    room_name = f"support-{ticket_id}"
    try:
        # Small delay to ensure DB transaction is committed
        await asyncio.sleep(0.5)
        created_name = await create_livekit_room(room_name)
        
        with Session(engine) as session:
            hr = session.exec(
                select(HelpRequest).where(HelpRequest.ticket_id == ticket_id)
            ).first()
            if hr:
                hr.room_url = created_name  # Store room name, not full URL
                session.add(hr)
                session.commit()
                print(f"[DB] Updated ticket {ticket_id} with room: {created_name}")
    except Exception as e:
        print(f"[ERROR] Failed to spawn room for ticket {ticket_id}: {e}")