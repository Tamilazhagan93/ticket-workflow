import html
import streamlit as st
from workflow import graph

st.set_page_config(page_title="IT Support", page_icon="🛠️", layout="centered")

# ---------- styles ----------
st.markdown("""
<style>
.badges {display:flex; gap:10px; flex-wrap:wrap; margin:8px 0 4px;}
.badge  {padding:6px 14px; border-radius:999px; font-size:14px; font-weight:600;
         background:#eef1f6; color:#2b2f36;}
.badge small {font-weight:400; opacity:.7; margin-right:6px;}
.p-Critical {background:#fde2e2; color:#b42318;}
.p-High     {background:#ffead5; color:#b54708;}
.p-Medium   {background:#fef7c3; color:#854a0e;}
.p-Low      {background:#dcfae6; color:#067647;}
.reply {line-height:1.6; font-size:15px;}
</style>
""", unsafe_allow_html=True)

# ---------- header ----------
st.title("🛠️ IT Support")
st.caption("Describe your problem and our AI assistant will reply by email.")

# ---------- form (= "On form submission" in n8n) ----------
with st.form("ticket_form", clear_on_submit=True):
    c1, c2 = st.columns(2)
    name = c1.text_input("Your name")
    email = c2.text_input("Email")
    subject = st.text_input("Subject")
    description = st.text_area("Describe the problem", height=140)
    submitted = st.form_submit_button("Submit ticket", type="primary", use_container_width=True)

# ---------- result ----------
if submitted:
    if not all([name, email, subject, description]):
        st.error("Please fill in all fields.")
        st.stop()

    with st.spinner("Our AI is working on your ticket..."):
        try:
            result = graph.invoke({"name": name, "email": email,
                                   "subject": subject, "description": description})
        except Exception as e:
            st.error(f"Something went wrong while processing the ticket: {e}")
            st.stop()

    category = result.get("category", "-")
    priority = result.get("priority", "-")
    team = result.get("team", "-")

    # ticket summary card
    with st.container(border=True):
        st.subheader("Ticket summary")
        if result.get("ticket_id"):
            st.caption(f"🎫 {result['ticket_id']}")
        st.markdown(f"""
        <div class="badges">
          <span class="badge"><small>Category</small>{html.escape(category)}</span>
          <span class="badge p-{html.escape(priority)}"><small>Priority</small>{html.escape(priority)}</span>
          <span class="badge"><small>Team</small>{html.escape(team)}</span>
        </div>
        """, unsafe_allow_html=True)
        if result.get("summary"):
            st.caption(result["summary"])
        if result.get("escalate"):
            st.warning(f"⚠️ Escalated to {team}: {result.get('escalation', '')}")

    # reply card
    with st.container(border=True):
        st.subheader("Reply")
        reply = html.escape(result.get("final_reply", "")).replace("\n", "<br>")
        st.markdown(f'<div class="reply">{reply}</div>', unsafe_allow_html=True)

    # email status
    if result.get("email_sent"):
        st.success(f"📧 Reply sent to {result.get('email')}")
    elif result.get("approved") is False:
        st.warning("Reply was not approved by review, so it was saved for a human agent.")
    else:
        st.warning("Email could not be sent. Check the terminal for the error.")

    # sheet status
    if result.get("sheet_saved"):
        st.info("📊 Ticket logged in Google Sheets")
    else:
        st.warning("Could not log the ticket in Google Sheets. Check the terminal.")

    with st.expander("Full state (debug)"):
        st.json(result)