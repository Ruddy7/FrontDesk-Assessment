def notify_supervisor(hr):
    print(f"[SUPERVISOR NOTIFY] Ticket {hr.ticket_id}: {hr.question}")


def notify_caller_followup(hr):
    if hr.supervisor_answer:
        print(f"[CALLER NOTIFY] {hr.caller}: {hr.supervisor_answer}")
    else:
        print(f"[CALLER NOTIFY] {hr.caller}: No answer available.")