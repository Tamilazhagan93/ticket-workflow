from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from llm import get_llm
from state import TicketState

llm = get_llm()


def ticket_text(state: TicketState) -> str:
    return (f"Subject: {state['subject']}\n"
            f"Description: {state['description']}\n"
            f"Category: {state['category']} | Priority: {state['priority']}")


# ---------------- AI 2: Resolution (plain text) ----------------
RESOLUTION_PROMPT = """You are an IT support resolution agent.
Write a reply that helps the user fix the problem themselves.
- Give 3 to 6 short numbered steps, simplest first.
- Use plain language, no jargon.
- Do NOT add a greeting or sign-off (they are added later).
- If the user cannot fix it themselves, say the IT team will handle it."""

def resolution(state: TicketState) -> dict:
    response = llm.invoke([SystemMessage(RESOLUTION_PROMPT), HumanMessage(ticket_text(state))])
    print("4a. resolution -> done")
    return {"resolution": response.text}


# ---------------- AI 3: Escalation (structured decision) ----------------
class EscalationResult(BaseModel):
    escalate: bool = Field(description="True if a human IT engineer must get involved")
    reason: str = Field(description="One short sentence explaining the decision")

ESCALATION_PROMPT = """You are an IT support escalation agent.
Decide if this ticket needs a human IT engineer.

Escalate when:
- hardware is physically broken
- many users are affected, or priority is Critical
- it is a security issue (hacked account, virus, phishing)
- it needs access/permission changes that require approval

Do NOT escalate simple how-to questions or problems the user can fix with basic steps."""

escalation_llm = llm.with_structured_output(EscalationResult)

def escalation(state: TicketState) -> dict:
    result = escalation_llm.invoke([SystemMessage(ESCALATION_PROMPT), HumanMessage(ticket_text(state))])
    print(f"4b. escalation -> escalate={result.escalate}")
    return {"escalate": result.escalate, "escalation": result.reason}

# ---------------- AI 4: Review (structured decision) ----------------
class ReviewResult(BaseModel):
    approved: bool = Field(description="True if the reply is good enough to send to the user")
    feedback: str = Field(description="If not approved: exactly what to fix. If approved: 'OK'")

REVIEW_PROMPT = """You are a senior IT support reviewer.
Check the draft reply against the ticket before it is emailed to the user.

Reject ONLY if there is a real problem:
- it does not address the user's actual problem
- steps are wrong, unsafe (e.g. disable antivirus, share a password) or made up
- it is confusing or unprofessional

Do not reject for small style preferences. A greeting and sign-off are added later, so do not ask for them."""

review_llm = llm.with_structured_output(ReviewResult)

def review(state: TicketState) -> dict:
    count = state.get("review_count", 0) + 1
    prompt = f"TICKET:\n{ticket_text(state)}\n\nDRAFT REPLY:\n{state['final_reply']}"
    result = review_llm.invoke([SystemMessage(REVIEW_PROMPT), HumanMessage(prompt)])
    print(f"6. review #{count} -> approved={result.approved} | {result.feedback}")
    return {"review_count": count, "approved": result.approved, "feedback": result.feedback}


# ---------------- Rewrite (Basic LLM Chain) ----------------
REWRITE_PROMPT = """You are an IT support writer.
Rewrite the draft reply so it fixes every point in the reviewer's feedback.
- Keep numbered steps and plain language.
- Keep any escalation note that is already in the draft.
- Do NOT add a greeting or sign-off.
- Return ONLY the new reply text."""

def rewrite(state: TicketState) -> dict:
    prompt = (f"TICKET:\n{ticket_text(state)}\n\n"
              f"DRAFT REPLY:\n{state['final_reply']}\n\n"
              f"REVIEWER FEEDBACK:\n{state['feedback']}")
    response = llm.invoke([SystemMessage(REWRITE_PROMPT), HumanMessage(prompt)])
    print("7. rewrite -> done")
    return {"final_reply": response.text}