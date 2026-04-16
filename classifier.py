"""
classifier.py - Ticket classification agent (Day 2)
Takes a raw support ticket and returns structured JSON:
category, urgency, entities, and routing.
"""

import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq()

# This is the system prompt - it tells the LLM how to behave.
# This is where prompt engineering lives.
SYSTEM_PROMPT = """You are a support ticket triage agent. 

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


def classify_ticket(ticket_text):
    """Send a ticket to the LLM and get structured classification back."""
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=300,
        temperature=0.1,  # Low temperature = more consistent, less creative
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": ticket_text}
        ]
    )
    
    raw_output = response.choices[0].message.content
    
    # Parse the JSON from the LLM's response
    try:
        result = json.loads(raw_output)
        return result
    except json.JSONDecodeError:
        return {"error": "Failed to parse LLM output", "raw": raw_output}


# --- Test with a sample ticket ---
if __name__ == "__main__":
    
    test_tickets = [
        {
            "name": "Angry login issue",
            "text": """Hi, my name is Sarah Chen. I've been trying to log into my account 
            for the past 2 hours and keep getting an "invalid credentials" error. 
            I've reset my password twice but nothing works. I have a presentation 
            tomorrow and I NEED access to my files urgently. If this isn't resolved 
            today I'm cancelling my subscription."""
        },
        {
            "name": "Billing question",
            "text": """Hello, I'm James Parker. I noticed I was charged $49.99 on my 
            last statement but I'm on the $29.99 plan. Could you look into this 
            and issue a refund for the difference? Thanks."""
        },
        {
            "name": "Feature request",
            "text": """Hey there! Love the product. Would be great if you could add 
            dark mode to the mobile app. A few of us in the office have been 
            talking about it. No rush, just a suggestion!"""
        }
    ]
    
    for ticket in test_tickets:
        print(f"\n{'='*50}")
        print(f"TICKET: {ticket['name']}")
        print(f"{'='*50}")
        result = classify_ticket(ticket["text"])
        print(json.dumps(result, indent=2))