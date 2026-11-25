import json
import urllib.request
import urllib.error
import sqlite3

API_URL = "http://localhost:3001/v1/chat/completions"
API_KEY = "freellmapi-cef1dbc78ced732f25a150aedb07869317e8dcece821acc6"

DB_FILE = "memory.db"

SYSTEM_PROMPT = """
You are a general-purpose fact-based AI agent.

Your job is to:
1. Understand the user's request.
2. Separate factual claims from opinions or creative content.
3. Never knowingly invent facts, sources, quotes, statistics, or events.
4. Clearly identify uncertainty when information cannot be verified.
5. Give useful, clear answers.
6. Distinguish verified information from inference.
"""

# Initialize memory database
def initialize_memory():
    db = sqlite3.connect(DB_FILE)
    db.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL
        )
    """)
    db.commit()
    db.close()

# Load recent conversation history
def load_memory():
    db = sqlite3.connect(DB_FILE)
    rows = db.execute("""
        SELECT role, content
        FROM conversations
        ORDER BY id DESC
        LIMIT 20
    """).fetchall()
    db.close()

    return [
        {"role": role, "content": content}
        for role, content in reversed(rows)
    ]

# Save a message
def save_memory(role, content):
    db = sqlite3.connect(DB_FILE)
    db.execute(
        "INSERT INTO conversations (role, content) VALUES (?, ?)",
        (role, content)
    )
    db.commit()
    db.close()

initialize_memory()

print("Fact Agent with Persistent Memory is running.")
print("Type 'exit' to quit.")

while True:
    user_input = input("\nYou: ")

    if user_input.lower() == "exit":
        break

    save_memory("user", user_input)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    messages.extend(load_memory())

    data = {
        "model": "auto",
        "messages": messages
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

        answer = result["choices"][0]["message"]["content"]

        print("\nAgent:", answer)

        save_memory("assistant", answer)

    except Exception as e:
        print("\nError:", e)

        # Remove the unsent user message from memory
        db = sqlite3.connect(DB_FILE)
        db.execute("""
            DELETE FROM conversations
            WHERE id = (
                SELECT MAX(id) FROM conversations
            )
        """)
        db.commit()
        db.close()

