import json
import urllib.request

API_URL = "http://localhost:3001/v1/chat/completions"
API_KEY = "freellmapi-cef1dbc78ced732f25a150aedb07869317e8dcece821acc6"

SYSTEM_PROMPT = """
You are a general-purpose fact-based AI agent.

Your job is to:
1. Understand the user's request.
2. Separate factual claims from opinions or creative content.
3. Never knowingly invent facts, sources, quotes, statistics, or events.
4. Clearly identify uncertainty when information cannot be verified.
5. Give useful, clear answers.
6. When research tools are added later, use sources and distinguish
   verified information from inference.
"""

print("Fact Agent is running.")
print("Type 'exit' to quit.")

while True:
    user_input = input("\nYou: ")

    if user_input.lower() == "exit":
        break

    data = {
        "model": "auto",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ]
    }

    request = urllib.request.Request(
        API_URL,
        data=json.dumps(data).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + API_KEY
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request) as response:
            result = json.loads(response.read().decode("utf-8"))

        print("\nAgent:", result["choices"][0]["message"]["content"])

    except Exception as e:
        print("\nError:", e)


