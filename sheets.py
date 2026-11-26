import os
from datetime import datetime
import gspread
from dotenv import load_dotenv

load_dotenv()

HEADERS = ["Date", "Ticket ID", "Name", "Email", "Subject",
           "Category", "Priority", "Team", "Escalated", "Status"]


def ticket_status(state) -> str:
    if state.get("email_sent"):
        return "Replied"
    if state.get("approved") is False:
        return "Needs Human"
    return "Email Failed"


def get_worksheet():
    gc = gspread.service_account(filename=os.getenv("GOOGLE_SA_FILE", "service_account.json"))
    return gc.open_by_key(os.getenv("GOOGLE_SHEET_ID")).sheet1


def append_ticket_row(state) -> None:
    ws = get_worksheet()
    if not ws.row_values(1):
        ws.append_row(HEADERS)
    ws.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        state.get("ticket_id", ""),
        state.get("name", ""),
        state.get("email", ""),
        state.get("subject", ""),
        state.get("category", ""),
        state.get("priority", ""),
        state.get("team", ""),
        "Yes" if state.get("escalate") else "No",
        ticket_status(state),
    ])