from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from llm import get_llm
from state import TicketState

class TriageResult(BaseModel):
    category: Literal["Hardware","Software","Network","Access","Email","Other"]=Field(
       description = "Which IT area the Problem belongs to")
    priority: Literal["Low","Medium","High","Critical"] = Field(
        description="How urgent the ticket is")
    summary: str = Field(description = "One short sentence describing the problem")    

TRIAGE_PROMPT = """you are an IT Support triage Agent
        Read the Ticket and classify it
        Priority guide:
       -Critical: many users affected or business stopped(server down, outage)
       -High: one user fully blocked from working
       -Medium: work is slowed but a workaround exists
       -Low: a question or minor request
       """
triage_llm = get_llm().with_structured_output(TriageResult)

def triage(state: TicketState) -> dict:
    ticket = f"Subject: {state['subject']}\nDescription: {state['description']}"
    result = triage_llm.invoke([SystemMessage(TRIAGE_PROMPT), HumanMessage(ticket)])
    print(f"1. triage -> {result.category} / {result.priority}")
    return result.model_dump()
    

