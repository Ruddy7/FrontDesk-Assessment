"""
Notification system for supervisors and callers.
In production, this would integrate with email, SMS, Slack, etc.
"""

def notify_supervisor(hr):
    """
    Notify supervisor about a new help request.
    Currently prints to console; in production would send email/SMS/Slack.
    """
    print(f"[SUPERVISOR NOTIFY] 🔔 New Ticket {hr.ticket_id}")
    print(f"  Caller: {hr.caller}")
    print(f"  Question: {hr.question}")
    print(f"  Time: {hr.created_at}")
    
    # TODO: In production, add:
    # - Send email to supervisor
    # - Send Slack notification
    # - Trigger SMS alert
    # - Push notification to mobile app


def notify_caller_followup(hr):
    """
    Notify caller about resolution or timeout.
    Currently prints to console; in production would send email/SMS.
    """
    if hr.state == "RESOLVED" and hr.supervisor_answer:
        print(f"[CALLER NOTIFY] ✅ {hr.caller} - Ticket {hr.ticket_id} Resolved")
        print(f"  Answer: {hr.supervisor_answer}")
    elif hr.state == "UNRESOLVED":
        print(f"[CALLER NOTIFY] ⏰ {hr.caller} - Ticket {hr.ticket_id} Timed Out")
        print(f"  Message: We apologize. A supervisor will follow up within 24 hours.")
    else:
        print(f"[CALLER NOTIFY] 📝 {hr.caller} - Update for Ticket {hr.ticket_id}")
        print(f"  Status: {hr.state}")
    
    # TODO: In production, add:
    # - Send email with answer
    # - Send SMS notification
    # - Update caller's app/portal