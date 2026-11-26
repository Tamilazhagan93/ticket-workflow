from datetime import datetime
from langgraph.graph import StateGraph, START, END
from state import TicketState
from triage import triage
from agents import resolution, escalation, review, rewrite
from gmail_sender import send_email
from sheets import append_ticket_row

MAX_REVIEWS = 3

TEAM_BY_CATEGORY = {"Hardware": "Desktop Team", "Software": "App Support",
                    "Network": "Network Team", "Access": "IAM Team",
                    "Email": "Messaging Team"}


def switch(state: TicketState):
    team = TEAM_BY_CATEGORY.get(state["category"], "General Support")
    print(f"2. switch -> {team}")
    return {"team": team}


def edit_fields(state: TicketState):
    ticket_id = "TKT-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    print(f"3. edit_fields -> {ticket_id}")
    return {"ticket_id": ticket_id,
            "email": state["email"].strip().lower(),
            "subject": state["subject"].strip()}


def merge(state: TicketState):
    reply = state["resolution"]
    if state.get("escalate"):
        reply += (f"\n\nWe have also escalated your ticket to our {state['team']} "
                  f"because: {state['escalation']}")
    print("5. merge")
    return {"final_reply": reply}


def send_gmail(state: TicketState):
    body = f"""Hi {state['name']},

Thank you for contacting IT Support. Here is the update on your ticket:

Ticket  : {state['ticket_id']}
Subject : {state['subject']}
Category: {state['category']} | Priority: {state['priority']}

{state['final_reply']}

Regards,
IT Support Team"""
    try:
        send_email(state["email"], f"[{state['ticket_id']}] Re: {state['subject']}", body)
        print(f"8. send_gmail -> sent to {state['email']}")
        return {"email_sent": True}
    except Exception as e:
        print(f"8. send_gmail -> FAILED: {e}")
        return {"email_sent": False}


def append_sheet(state: TicketState):
    try:
        append_ticket_row(state)
        print("9. append_sheet -> row added")
        return {"sheet_saved": True}
    except Exception as e:
        print(f"9. append_sheet -> FAILED: {e}")
        return {"sheet_saved": False}


# ---- the "If" node ----
def after_review(state: TicketState) -> str:
    if state["approved"]:
        return "send_gmail"
    if state["review_count"] >= MAX_REVIEWS:
        return "append_sheet"      # give up: log for a human, don't email
    return "rewrite"


# ---- wiring ----
g = StateGraph(TicketState)
for name, fn in [("triage", triage), ("switch", switch), ("edit_fields", edit_fields),
                 ("resolution", resolution), ("escalation", escalation), ("merge", merge),
                 ("review", review), ("rewrite", rewrite),
                 ("send_gmail", send_gmail), ("append_sheet", append_sheet)]:
    g.add_node(name, fn)

g.add_edge(START, "triage")
g.add_edge("triage", "switch")
g.add_edge("switch", "edit_fields")
g.add_edge("edit_fields", "resolution")
g.add_edge("edit_fields", "escalation")
g.add_edge(["resolution", "escalation"], "merge")
g.add_edge("merge", "review")
g.add_conditional_edges("review", after_review,
                        {"send_gmail": "send_gmail", "rewrite": "rewrite",
                         "append_sheet": "append_sheet"})
g.add_edge("rewrite", "review")
g.add_edge("send_gmail", "append_sheet")
g.add_edge("append_sheet", END)

graph = g.compile()

if __name__ == "__main__":
    result = graph.invoke({"name": "Tamil", "email": "YOUR_EMAIL@gmail.com",
                           "subject": "LAN cable issue",
                           "description": "My PC shows no internet after I moved desks."})
    print("-" * 40)
    print("Final state:", result)