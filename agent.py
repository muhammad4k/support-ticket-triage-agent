"""
agent.py - Full triage agent (Day 3)
Step 1: Classify the ticket (category, urgency, entities)
Step 2: Draft a customer response based on the classification
This is the agent loop - classify then act.
"""

import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq()

# --- Step 1: Classification (same as before) ---

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


# --- Step 2: Response drafter ---

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


def classify_ticket(ticket_text):
    """Step 1: Classify the ticket."""
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
    """Step 2: Draft a reply based on classification."""
    context = f"""Original ticket:
{ticket_text}

Classification:
{json.dumps(classification, indent=2)}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=300,
        temperature=0.4,  # Slightly more creative for natural-sounding replies
        messages=[
            {"role": "system", "content": RESPONSE_PROMPT},
            {"role": "user", "content": context}
        ]
    )
    return response.choices[0].message.content


def triage_ticket(ticket_text):
    """Full agent loop: classify → draft response."""
    print("\n[STEP 1] Classifying ticket...")
    classification = classify_ticket(ticket_text)
    print(json.dumps(classification, indent=2))

    if "error" in classification:
        print("Classification failed. Cannot draft response.")
        return

    print("\n[STEP 2] Drafting response...")
    response = draft_response(ticket_text, classification)
    print(response)

    print(f"\n[ROUTING] → This ticket goes to: {classification['route_to']}")
    print(f"[URGENCY] → {classification['urgency'].upper()}")

    return {
        "classification": classification,
        "drafted_response": response
    }


# --- Test it ---
if __name__ == "__main__":

    test_tickets = [
        """Hi, my name is Sarah Chen. I've been trying to log into my account 
        for the past 2 hours and keep getting an "invalid credentials" error. 
        I've reset my password twice but nothing works. I have a presentation 
        tomorrow and I NEED access to my files urgently. If this isn't resolved 
        today I'm cancelling my subscription.""",

        """Hello, I'm James Parker. I noticed I was charged $49.99 on my 
        last statement but I'm on the $29.99 plan. Could you look into this 
        and issue a refund for the difference? Thanks.""",

        """Hey there! Love the product. Would be great if you could add 
        dark mode to the mobile app. A few of us in the office have been 
        talking about it. No rush, just a suggestion!"""
    ]

    for i, ticket in enumerate(test_tickets, 1):
        print(f"\n{'='*60}")
        print(f"TICKET {i}")
        print(f"{'='*60}")
        triage_ticket(ticket)