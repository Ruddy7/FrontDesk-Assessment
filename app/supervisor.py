from datetime import datetime
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
import os

from .db import engine, HelpRequest, KBEntry
from .notifications import notify_caller_followup
from .agent import generate_access_token


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# --- Admin dashboard ---
@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    with Session(engine) as session:
        pending = session.exec(
            select(HelpRequest).where(HelpRequest.state == "PENDING")
        ).all()
        resolved = session.exec(
            select(HelpRequest).where(HelpRequest.state != "PENDING")
        ).all()
        kb = session.exec(select(KBEntry)).all()

    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "pending_requests": pending,
            "resolved_requests": resolved,
            "kb": kb,
        },
    )


# --- Supervisor join voice call ---
@router.get("/admin/join_call/{ticket_id}")
async def supervisor_join_call(ticket_id: str):
    """
    Generate a LiveKit token for supervisor to join the voice call.
    Returns JSON with connection details.
    """
    with Session(engine) as session:
        hr = session.exec(
            select(HelpRequest).where(HelpRequest.ticket_id == ticket_id)
        ).first()

        if not hr:
            return JSONResponse(
                {"error": "Ticket not found"},
                status_code=404
            )

        if not hr.room_url:
            return JSONResponse(
                {"error": "Room not created yet. Ask caller to connect first."},
                status_code=400
            )

        # Generate supervisor token
        import uuid
        supervisor_identity = f"supervisor-{uuid.uuid4().hex[:8]}"
        token = generate_access_token(
            identity=supervisor_identity,
            room_name=hr.room_url,
            role="supervisor"
        )

        print(f"[SUPERVISOR] Joining call for ticket {ticket_id}, room: {hr.room_url}")

        return JSONResponse({
            "url": os.getenv("LIVEKIT_URL"),
            "room": hr.room_url,
            "token": token,
            "identity": supervisor_identity,
            "caller": hr.caller,
            "question": hr.question
        })


# --- Resolve help request ---
@router.post("/admin/resolve")
async def resolve_request(ticket_id: str = Form(...), answer: str = Form(...)):
    with Session(engine) as session:
        hr = session.exec(
            select(HelpRequest).where(HelpRequest.ticket_id == ticket_id)
        ).first()

        if not hr:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # Update help request
        hr.supervisor_answer = answer
        hr.state = "RESOLVED"
        hr.resolved_at = datetime.utcnow()
        session.add(hr)

        # Update or insert KB entry
        kb_entry = session.exec(
            select(KBEntry).where(KBEntry.question == hr.question)
        ).first()

        if kb_entry:
            kb_entry.answer = answer
        else:
            session.add(KBEntry(question=hr.question, answer=answer))

        session.commit()

        # Notify the caller about resolution
        notify_caller_followup(hr)

    return RedirectResponse(url="/admin", status_code=303)


# --- Add KB entry manually ---
@router.post("/admin/kb/add")
async def add_kb_entry(question: str = Form(...), answer: str = Form(...)):
    with Session(engine) as session:
        # Check if exists
        existing = session.exec(
            select(KBEntry).where(KBEntry.question == question)
        ).first()

        if existing:
            existing.answer = answer
        else:
            session.add(KBEntry(question=question, answer=answer))
        
        session.commit()

    return RedirectResponse(url="/admin", status_code=303)


# --- Delete KB entry ---
@router.post("/admin/kb/delete")
async def delete_kb_entry(kb_id: int = Form(...)):
    with Session(engine) as session:
        kb = session.get(KBEntry, kb_id)
        if kb:
            session.delete(kb)
            session.commit()

    return RedirectResponse(url="/admin", status_code=303)