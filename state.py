from typing import TypedDict

class TicketState(TypedDict, total=False):
    #--form input --
    name: str
    email: str
    subject: str
    description: str
    #--AI 1 Triage---
    category: str
    priority: str
    summary: str
    #---switch ---
    team: str
    #--AI2/ AI3(parallel : each writes its OWN key, so no clash)---
    resolution: str
    escalation:str
    escalate: bool          # ← needed by the escalation agent
    #--merge+ AI4 review
    final_reply: str
    approved: bool
    feedback: str
    review_count: int
    # --- output ---
    email_sent: bool        # ← needed by send_gmail
    ticket_id: str
    sheet_saved: bool