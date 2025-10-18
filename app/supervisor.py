from datetime import datetime
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select
from .db import engine, HelpRequest, KBEntry
from .notifications import notify_caller_followup

router = APIRouter()


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    with Session(engine) as session:
        pending = session.exec(select(HelpRequest).where(HelpRequest.state == "PENDING")).all()
        resolved = session.exec(select(HelpRequest).where(HelpRequest.state != "PENDING")).all()
        kb = session.exec(select(KBEntry)).all()

    # Render dynamic HTML (replace later with Jinja2 if you want templates)
    html = "<html><body><h2>Supervisor Panel</h2>"

    html += "<h3>Pending Requests</h3>"
    for p in pending:
        html += f"<div><strong>{p.ticket_id}</strong> from {p.caller}: {p.question}<br>"
        if p.room_url:
            html += f"<a href='{p.room_url}' target='_blank'>🎥 Join Live Room</a><br>"
        html += (
            f"<form method='post' action='/admin/resolve'>"
            f"<input type='hidden' name='ticket_id' value='{p.ticket_id}'/>"
            f"<input name='answer' placeholder='Answer here'/><button type='submit'>Submit</button></form></div>"
        )

    html += "<h3>Resolved / Unresolved</h3>"
    for r in resolved:
        html += f"<div>{r.ticket_id} — {r.state} — Answer: {r.supervisor_answer}</div>"

    html += "</body></html>"
    return HTMLResponse(html)


@router.post("/admin/resolve")
async def resolve_request(ticket_id: str = Form(...), answer: str = Form(...)):
    with Session(engine) as session:
        hr = session.exec(select(HelpRequest).where(HelpRequest.ticket_id == ticket_id)).first()
        if not hr:
            raise HTTPException(status_code=404, detail="Ticket not found")
        hr.supervisor_answer = answer
        hr.state = "RESOLVED"
        hr.resolved_at = datetime.utcnow()
        session.add(hr)

        # Update KB
        kb_entry = session.exec(select(KBEntry).where(KBEntry.question == hr.question)).first()
        if kb_entry:
            kb_entry.answer = answer
        else:
            session.add(KBEntry(question=hr.question, answer=answer))

        session.commit()
        notify_caller_followup(hr)

    return RedirectResponse(url="/admin", status_code=303)
