import os
import uuid
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from .db import engine, KBEntry, HelpRequest
from .agent import find_in_kb, create_help_request, generate_access_token
from .background import start_worker
from .supervisor import router as supervisor_router


app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(supervisor_router)

templates = Jinja2Templates(directory="app/templates")


# --- Startup event ---
@app.on_event("startup")
async def startup():
    with Session(engine) as session:
        if not session.exec(select(KBEntry)).first():
            session.add(KBEntry(question="Opening hours", answer="9am-7pm Tue-Sat"))
            session.add(KBEntry(question="Walk-ins?", answer="Yes, but appointments preferred"))
            session.commit()

    start_worker()


# --- Caller form route ---
@app.get("/", response_class=HTMLResponse)
async def caller_form(request: Request):
    return templates.TemplateResponse("caller.html", {"request": request})


# --- Call submission ---
@app.post("/call", response_class=HTMLResponse)
async def receive_call(request: Request, caller: str = Form(...), question: str = Form(...)):
    entry = find_in_kb(question)

    if entry:
        return HTMLResponse(f"<div>AI Reply: {entry.answer}</div>")
    else:
        hr = create_help_request(caller, question)

        # Return caller page with ticket ID so frontend can join voice
        return templates.TemplateResponse(
            "caller.html",
            {
                "request": request,
                "ticket_id": hr.ticket_id,
                "message": "AI: No direct answer found. A supervisor will join shortly via LiveKit.",
            },
        )


# --- LiveKit join token ---
@app.get("/join_token/{ticket_id}")
async def join_token(ticket_id: str, role: str = "caller"):
    """
    Return a LiveKit join token and connection info for the given ticket.
    role: 'caller' or 'supervisor'
    """
    import asyncio
    
    with Session(engine) as session:
        hr = session.exec(
            select(HelpRequest).where(HelpRequest.ticket_id == ticket_id)
        ).first()

        if not hr:
            return JSONResponse({"error": "ticket not found"}, status_code=404)

        # Wait a bit for room to be created if not yet available
        max_retries = 10
        for i in range(max_retries):
            if hr.room_url:
                break
            await asyncio.sleep(0.5)
            session.refresh(hr)
        
        # Use the room name from DB, or create default
        room_name = hr.room_url if hr.room_url else f"support-{ticket_id}"

        # Generate an identity and token
        identity = f"{role}-{uuid.uuid4().hex[:8]}"
        token = generate_access_token(identity=identity, room_name=room_name, role=role)

        print(f"[JOIN TOKEN] Generated for ticket {ticket_id}, room: {room_name}, identity: {identity}")

        return {
            "url": os.getenv("LIVEKIT_URL"),
            "room": room_name,
            "token": token,
            "identity": identity,
        }