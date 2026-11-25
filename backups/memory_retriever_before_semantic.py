import sqlite3
import re

DB_FILE = "long_term_memory.db"

def retrieve_memories(query="", limit=8):
    try:
        with sqlite3.connect(DB_FILE) as db:
            rows = db.execute("""
                SELECT id, category, fact
                FROM memories
            """).fetchall()

        if not rows:
            return ""

        words = set(re.findall(r"\b[a-z0-9]+\b", query.lower()))
        scored = []

        for memory_id, category, fact in rows:
            text = (category + " " + fact).lower()
            memory_words = set(re.findall(r"\b[a-z0-9]+\b", text))

            score = len(words & memory_words)

            if score > 0 or not words:
                scored.append((score, memory_id, category, fact))

        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)

        return "\n".join(
            f"- [{category}] {fact}"
            for score, memory_id, category, fact
            in scored[:limit]
        )

    except Exception as error:
        print("Memory retrieval error:", error)
        return ""
