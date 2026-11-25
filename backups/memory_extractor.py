import json
import sqlite3
import urllib.request

DB_FILE = "long_term_memory.db"

def extract_memories(user_message, api_url, api_key):
    prompt = """
Extract useful, lasting facts explicitly stated by the user.

Return ONLY valid JSON:
[
  {
    "category": "Project",
    "fact": "User is developing Fact Agent using Python."
  }
]

Return [] if there is nothing worth remembering.
Never invent facts.
"""

    data = {
        "model": "auto",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_message}
        ]
    }

    request = urllib.request.Request(
        api_url,
        data=json.dumps(data).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request) as response:
            result = json.loads(response.read().decode("utf-8"))

        content = result["choices"][0]["message"]["content"]
        start = content.find("[")
        end = content.rfind("]")

        if start == -1 or end == -1:
            print("No memories extracted.")
            return

        memories = json.loads(content[start:end + 1])

        if not isinstance(memories, list):
            return

        with sqlite3.connect(DB_FILE) as db:
            for item in memories:
                if not isinstance(item, dict):
                    continue

                category = item.get("category")
                fact = item.get("fact")

                if not isinstance(category, str) or not isinstance(fact, str):
                    continue

                category = category.strip()
                fact = fact.strip()

                if not category or not fact or len(fact) > 500:
                    continue

                db.execute("""
                    INSERT INTO memories (category, fact)
                    SELECT ?, ?
                    WHERE NOT EXISTS (
                        SELECT 1 FROM memories WHERE fact = ?
                    )
                """, (category, fact, fact))

        print("Memory extraction completed.")

    except Exception as error:
        print("Memory extraction error:", error)
