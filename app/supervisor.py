from datetime import datetime
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from .db import engine, HelpRequest, KBEntry
from .notifications import notify_caller_followup


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
