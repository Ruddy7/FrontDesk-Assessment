from datetime import datetime
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from .db import engine, HelpRequest, KBEntry
from sqlmodel import Session, select
from .notifications import notify_caller_followup


router = APIRouter()


@router.get("/admin", response_class=HTMLResponse)
async def admin_page():
    with Session(engine) as session:
        pending = session.exec(select(HelpRequest).where(HelpRequest.state == "PENDING")).all()
        resolved = session.exec(select(HelpRequest).where(HelpRequest.state != "PENDING")).all()
        kb = session.exec(select(KBEntry)).all()
    # Render using templates (caller.html / admin.html)
    # Simplified: raw HTML returned
    html = "<html><body><h2>Supervisor Panel</h2>"
    html += "<h3>Pending Requests</h3>"
    for p in pending:
        html += f"<div>{p.ticket_id} from {p.caller}: {p.question}<form method='post' action='/admin/resolve'>"
        html += f"<input type='hidden' name='ticket_id' value='{p.ticket_id}'/>"
        html += "<input name='answer' placeholder='Answer here'/><button type='submit'>Submit</button></form></div>"
    html += "<h3>Resolved / Unresolved</h3>"
    for r in resolved:
        html += f"<div>{r.ticket_id} — {r.state} — Answer: {r.supervisor_answer}</div>"
    html += "</body></html>"
    return HTMLResponse(html)


@router.post("/admin/resolve")
async def resolve_request(ticket_id: str = Form(...), answer: str = Form(...)):
    with Session(engine) as session:
        stmt = select(HelpRequest).where(HelpRequest.ticket_id == ticket_id)
        hr = session.exec(stmt).first()
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
            session.add(kb_entry)
        else:
            session.add(KBEntry(question=hr.question, answer=answer))
        session.commit()
        notify_caller_followup(hr)
    return RedirectResponse(url="/admin", status_code=303)