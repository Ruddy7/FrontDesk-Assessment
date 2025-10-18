import threading, time
from datetime import datetime, timedelta
from sqlmodel import Session, select
from .db import HelpRequest, engine
from .notifications import notify_caller_followup

SUPERVISOR_TIMEOUT_SECONDS = 300  # 5 min


def timeout_worker():
    while True:
        with Session(engine) as session:
            pending = session.exec(
                select(HelpRequest).where(HelpRequest.state == "PENDING")
            ).all()
            for hr in pending:
                if datetime.utcnow() - hr.created_at > timedelta(seconds=SUPERVISOR_TIMEOUT_SECONDS):
                    hr.state = "UNRESOLVED"
                    hr.resolved_at = datetime.utcnow()
                    session.add(hr)
                    session.commit()
                    notify_caller_followup(hr)
                    print(f"[Timeout] Ticket {hr.ticket_id} marked UNRESOLVED")
        time.sleep(30)


def start_worker():
    t = threading.Thread(target=timeout_worker, daemon=True)
    t.start()
    print("[Background] Timeout worker started.")
