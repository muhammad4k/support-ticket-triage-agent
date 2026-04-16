import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq()

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    max_tokens=200,
    messages=[
        {"role": "user", "content": "In one sentence, what is a customer support ticket?"}
    ]
)

print(response.choices[0].message.content)