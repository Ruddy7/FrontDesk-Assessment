from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from .agent import find_in_kb, create_help_request
from .background import start_worker
from .supervisor import router as supervisor_router
from .db import engine, SQLModel, KBEntry
from sqlmodel import Session, select


app = FastAPI()
app.include_router(supervisor_router)


@app.on_event("startup")
async def startup():
    # Seed KB
    with Session(engine) as session:
        if not session.exec(select(KBEntry)).first():
            session.add(KBEntry(question="Opening hours", answer="9am-7pm Tue-Sat"))
            session.add(KBEntry(question="Walk-ins?", answer="Yes, but appointments preferred"))
            session.commit()
    start_worker()


@app.get("/", response_class=HTMLResponse)
async def caller_form():
    return """<html><body><h2>Caller Form</h2><form action='/call' method='post'>Name:<input name='caller'/><br/>Question:<input name='question'/><button type='submit'>Submit</button></form></body></html>"""


@app.post("/call", response_class=HTMLResponse)
async def receive_call(caller: str = Form(...), question: str = Form(...)):
    entry = find_in_kb(question)
    if entry:
        return HTMLResponse(f"<div>AI Reply: {entry.answer}</div>")
    else:
        create_help_request(caller, question)
        return HTMLResponse(f"<div>AI: Let me check with supervisor (ticket created)</div>")