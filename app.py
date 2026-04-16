"""
app.py - Streamlit UI for the Support Ticket Triage Agent
Paste a ticket → watch the agent classify → see the drafted response
"""

import os
import json
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq()

# --- Prompts ---

CLASSIFIER_PROMPT = """You are a support ticket triage agent. 

When given a customer support ticket, analyze it and respond with ONLY a JSON object (no other text) in this exact format:

{
    "category": "billing" | "technical" | "account" | "product" | "general",
    "urgency": "high" | "medium" | "low",
    "customer_name": "extracted name or null",
    "issue_summary": "one sentence summary of the issue",
    "route_to": "billing_team" | "technical_support" | "account_management" | "product_team" | "general_support"
}

Rules:
- "high" urgency: service is down, security issue, or customer is threatening to leave
- "medium" urgency: feature not working, billing discrepancy, or account change needed  
- "low" urgency: general question, feedback, or feature request
- Route to the team that matches the category
- Extract the customer name if mentioned, otherwise null
- Keep issue_summary under 20 words"""

RESPONSE_PROMPT = """You are a friendly, professional customer support agent. 

You will receive:
1. The original customer ticket
2. The classification data (category, urgency, route)

Write a helpful reply to the customer. Follow these rules:
- If you know their name, use it. Otherwise say "Hi there"
- Acknowledge their issue specifically (don't be generic)
- For HIGH urgency: express urgency, give immediate next steps, provide a timeline
- For MEDIUM urgency: be helpful and clear, give a timeline of 1-2 business days
- For LOW urgency: be warm and appreciative, no rush in tone
- Keep it under 100 words
- Sign off as "Support Team"
- Do NOT use markdown formatting, just plain text"""

# --- Sample tickets ---

SAMPLE_TICKETS = {
    "😡 Angry login issue (HIGH)": """Hi, my name is Sarah Chen. I've been trying to log into my account for the past 2 hours and keep getting an "invalid credentials" error. I've reset my password twice but nothing works. I have a presentation tomorrow and I NEED access to my files urgently. If this isn't resolved today I'm cancelling my subscription.""",
    
    "💳 Billing discrepancy (MEDIUM)": """Hello, I'm James Parker. I noticed I was charged $49.99 on my last statement but I'm on the $29.99 plan. Could you look into this and issue a refund for the difference? Thanks.""",
    
    "💡 Feature request (LOW)": """Hey there! Love the product. Would be great if you could add dark mode to the mobile app. A few of us in the office have been talking about it. No rush, just a suggestion!""",
    
    "🔒 Security concern (HIGH)": """URGENT: I just received an email saying my account password was changed, but I didn't do this. I think someone has hacked into my account. My name is Priya Sharma and my account email is priya.s@email.com. Please lock my account immediately.""",
    
    "📦 Product issue (MEDIUM)": """Hi, I'm Tom Wilson. The export feature in the dashboard has been broken since last week's update. When I click "Export to CSV" nothing happens. I need this for my weekly reports. Can someone look into it?"""
}

# --- Agent functions ---

def classify_ticket(ticket_text):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=300,
        temperature=0.1,
        messages=[
            {"role": "system", "content": CLASSIFIER_PROMPT},
            {"role": "user", "content": ticket_text}
        ]
    )
    raw = response.choices[0].message.content
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"error": "Failed to parse", "raw": raw}


def draft_response(ticket_text, classification):
    context = f"""Original ticket:
{ticket_text}

Classification:
{json.dumps(classification, indent=2)}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=300,
        temperature=0.4,
        messages=[
            {"role": "system", "content": RESPONSE_PROMPT},
            {"role": "user", "content": context}
        ]
    )
    return response.choices[0].message.content


# --- Streamlit UI ---

st.set_page_config(page_title="Ticket Triage Agent", page_icon="🎫", layout="wide")

# Sidebar
with st.sidebar:
    st.header("📋 Sample Tickets")
    st.caption("Click any sample to load it, or write your own.")
    for label, text in SAMPLE_TICKETS.items():
        if st.button(label, use_container_width=True):
            st.session_state["ticket"] = text

st.title("🎫 Support Ticket Triage Agent")
st.markdown("Paste a customer support ticket below and watch the agent classify it, draft a response, and route it to the right team.")

# Text input
ticket_input = st.text_area(
    "Paste a support ticket:",
    value=st.session_state.get("ticket", ""),
    height=150,
    placeholder="e.g. Hi, my name is Sarah Chen. I've been trying to log into my account..."
)

# Triage button
if st.button("🚀 Triage This Ticket", type="primary"):
    if not ticket_input.strip():
        st.warning("Please paste a ticket first.")
    else:
        # Step 1: Classify
        with st.status("🔍 Step 1: Classifying ticket...", expanded=True) as status:
            classification = classify_ticket(ticket_input)

            if "error" in classification:
                st.error(f"Classification failed: {classification}")
                st.stop()

            col1, col2, col3 = st.columns(3)

            urgency_colors = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            urgency = classification.get("urgency", "unknown")

            col1.metric("Category", classification.get("category", "N/A").upper())
            col2.metric("Urgency", f"{urgency_colors.get(urgency, '⚪')} {urgency.upper()}")
            col3.metric("Route To", classification.get("route_to", "N/A").replace("_", " ").title())

            if classification.get("customer_name"):
                st.info(f"👤 Customer: **{classification['customer_name']}**")

            st.caption(f"📋 Summary: {classification.get('issue_summary', 'N/A')}")

            status.update(label="✅ Classification complete", state="complete")

        # Step 2: Draft response
        with st.status("✍️ Step 2: Drafting response...", expanded=True) as status:
            response = draft_response(ticket_input, classification)
            st.markdown("**Drafted reply:**")
            st.text(response)
            status.update(label="✅ Response drafted", state="complete")

        # Final routing box
        st.success(f"✅ Ticket triaged → Routed to **{classification.get('route_to', 'N/A').replace('_', ' ').title()}** with **{urgency.upper()}** urgency")