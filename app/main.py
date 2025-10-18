from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from .db import engine, KBEntry
from .agent import find_in_kb, create_help_request
from .background import start_worker
from .supervisor import router as supervisor_router

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(supervisor_router)
templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
async def startup():
    with Session(engine) as session:
        if not session.exec(select(KBEntry)).first():
            session.add(KBEntry(question="Opening hours", answer="9am-7pm Tue-Sat"))
            session.add(KBEntry(question="Walk-ins?", answer="Yes, but appointments preferred"))
            session.commit()
    start_worker()


@app.get("/", response_class=HTMLResponse)
async def caller_form(request: Request):
    return templates.TemplateResponse("caller.html", {"request": request})


@app.post("/call", response_class=HTMLResponse)
async def receive_call(request: Request, caller: str = Form(...), question: str = Form(...)):
    entry = find_in_kb(question)
    if entry:
        return HTMLResponse(f"<div>AI Reply: {entry.answer}</div>")
    else:
        create_help_request(caller, question)
        return HTMLResponse(
            "<div>AI: No direct answer found. A supervisor will join shortly via LiveKit.</div>"
        )
