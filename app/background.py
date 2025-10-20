"""
Background worker for handling timeouts and cleanup tasks.
"""
import threading
import time
from datetime import datetime, timedelta
from sqlmodel import Session, select
from .db import HelpRequest, engine
from .notifications import notify_caller_followup

# Timeout settings
SUPERVISOR_TIMEOUT_SECONDS = 300  # 5 minutes
CHECK_INTERVAL_SECONDS = 30  # Check every 30 seconds


def timeout_worker():
    """
    Background thread that checks for timed-out help requests.
    Marks requests as UNRESOLVED if no supervisor responds within timeout period.
    """
    print(f"[Background] Worker started. Checking every {CHECK_INTERVAL_SECONDS}s for timeouts > {SUPERVISOR_TIMEOUT_SECONDS}s")
    
    while True:
        try:
            with Session(engine) as session:
                # Find all pending requests
                pending = session.exec(
                    select(HelpRequest).where(HelpRequest.state == "PENDING")
                ).all()
                
                current_time = datetime.utcnow()
                
                for hr in pending:
                    # Check if request has timed out
                    elapsed = current_time - hr.created_at
                    
                    if elapsed > timedelta(seconds=SUPERVISOR_TIMEOUT_SECONDS):
                        print(f"[Timeout] ⏰ Ticket {hr.ticket_id} exceeded {SUPERVISOR_TIMEOUT_SECONDS}s")
                        
                        # Mark as unresolved
                        hr.state = "UNRESOLVED"
                        hr.resolved_at = current_time
                        hr.supervisor_answer = "This request timed out. A supervisor will follow up within 24 hours."
                        
                        session.add(hr)
                        session.commit()
                        
                        # Notify the caller
                        notify_caller_followup(hr)
                        
                        print(f"[Timeout] Ticket {hr.ticket_id} marked UNRESOLVED and caller notified")
        
        except Exception as e:
            print(f"[Background] Error in timeout worker: {e}")
            # Continue running even if there's an error
        
        # Sleep before next check
        time.sleep(CHECK_INTERVAL_SECONDS)


def start_worker():
    """
    Start the background timeout worker thread.
    This is called during application startup.
    """
    worker_thread = threading.Thread(target=timeout_worker, daemon=True)
    worker_thread.start()
    print("[Background] ✓ Timeout worker thread started")