#!/usr/bin/env python3
"""Fact Agent - A fact-based AI agent with persistent memory."""

import json
import sys
import sqlite3
from pathlib import Path

from fact_agent.config import get_settings
from fact_agent.http_client import LLMClient
from fact_agent.memory_extractor import extract_and_store
from fact_agent.memory_retriever import retrieve_memories
from fact_agent.memory_consolidator import MemoryConsolidator
from fact_agent.logging_setup import setup_logging, get_logger
from fact_agent.tools import get_tool_registry, ToolResult
from fact_agent.streaming import stream_response

logger = get_logger(__name__)

# Initialize settings early
settings = get_settings()
setup_logging(settings)

# Initialize tool registry
tool_registry = get_tool_registry()


def initialize_memory(db_path: Path | None = None) -> None:
    """Initialize the conversation memory database."""
    path = db_path or settings.memory_db_path
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Add created_at column if missing (migration)
        cursor = db.execute("PRAGMA table_info(conversations)")
        cols = {row[1] for row in cursor.fetchall()}
        if "created_at" not in cols:
            # SQLite doesn't allow DEFAULT in ALTER TABLE, so add without default then update
            db.execute("ALTER TABLE conversations ADD COLUMN created_at TIMESTAMP")
            db.execute("UPDATE conversations SET created_at = datetime('now')")
            # Recreate table with proper default for future inserts
            db.execute("""
                CREATE TABLE conversations_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("""
                INSERT INTO conversations_new (id, role, content, created_at)
                SELECT id, role, content, created_at FROM conversations
            """)
            db.execute("DROP TABLE conversations")
            db.execute("ALTER TABLE conversations_new RENAME TO conversations")

        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_created
            ON conversations(created_at)
        """)
        db.commit()

    logger.debug("Memory database initialized", extra={"path": str(path)})


def load_memory(limit: int | None = None, db_path: Path | None = None) -> list[dict[str, str]]:
    """Load recent conversation history."""
    limit = limit or settings.conversation_limit
    path = db_path or settings.memory_db_path

    try:
        with sqlite3.connect(path) as db:
            rows = db.execute("""
                SELECT role, content
                FROM conversations
                ORDER BY id DESC
                LIMIT ?
            """, (limit,)).fetchall()

        return [
            {"role": role, "content": content}
            for role, content in reversed(rows)
        ]
    except sqlite3.Error as e:
        logger.error("Failed to load memory", exc_info=e)
        return []


def save_memory(role: str, content: str, db_path: Path | None = None) -> None:
    """Save a message to conversation memory."""
    path = db_path or settings.memory_db_path

    try:
        with sqlite3.connect(path) as db:
            db.execute(
                "INSERT INTO conversations (role, content) VALUES (?, ?)",
                (role, content),
            )
            db.commit()
    except sqlite3.Error as e:
        logger.error("Failed to save memory", exc_info=e)


def remove_last_message(db_path: Path | None = None) -> None:
    """Remove the most recent message (used on API failure)."""
    path = db_path or settings.memory_db_path

    try:
        with sqlite3.connect(path) as db:
            db.execute("""
                DELETE FROM conversations
                WHERE id = (SELECT MAX(id) FROM conversations)
            """)
            db.commit()
    except sqlite3.Error as e:
        logger.error("Failed to remove last message", exc_info=e)


def build_messages(user_input: str, llm_client: LLMClient) -> list[dict[str, str]]:
    """Build the message list for LLM request."""
    messages = [{"role": "system", "content": settings.system_prompt}]

    # Add conversation history
    messages.extend(load_memory())

    # Add relevant long-term memories
    long_term = retrieve_memories(
        query=user_input,
        client=llm_client,
    )
    if long_term:
        messages.append({
            "role": "system",
            "content": f"Relevant long-term memories about the user:\n{long_term}"
        })

    # Add current user input
    messages.append({"role": "user", "content": user_input})

    return messages


def build_messages_with_tools(user_input: str, llm_client: LLMClient) -> list[dict]:
    """Build message list including tool specifications."""
    messages = [{"role": "system", "content": settings.system_prompt + "\n\nYou have access to tools. Use them when needed to answer questions accurately."}]

    # Add conversation history
    messages.extend(load_memory())

    # Add relevant long-term memories
    long_term = retrieve_memories(
        query=user_input,
        client=llm_client,
    )
    if long_term:
        messages.append({
            "role": "system",
            "content": f"Relevant long-term memories about the user:\n{long_term}"
        })

    # Add current user input
    messages.append({"role": "user", "content": user_input})

    return messages


def main() -> int:
    """Main agent loop."""
    print("Fact Agent with Persistent Memory is running.")
    print("Type 'exit' or 'quit' to quit.\n")

    # Initialize databases
    initialize_memory()

    # Create LLM client
    llm_client = LLMClient(
        api_url=settings.llm_api_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        timeout=settings.llm_timeout,
    )

    # Initialize memory consolidator
    consolidator = MemoryConsolidator(client=llm_client)
    exchange_count = 0

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        if not user_input:
            continue

        # Save user message
        save_memory("user", user_input)

        # Build messages with context
        messages = build_messages_with_tools(user_input, llm_client)

        # Request completion with tool support and streaming
        try:
            print("\nAgent: ", end="", flush=True)
            answer_chunks = []
            for chunk in stream_response(
                llm_client,
                messages,
                tools=tool_registry.get_function_specs(),
            ):
                print(chunk, end="", flush=True)
                answer_chunks.append(chunk)
            print()  # Newline after streaming
            answer = "".join(answer_chunks)

            # Save assistant response
            save_memory("assistant", answer)

            exchange_count += 1

            # Extract and store long-term memories
            if settings.enable_memory_extraction:
                try:
                    count = extract_and_store(user_input, llm_client)
                    if count > 0:
                        logger.info("Extracted new memories", extra={"count": count})
                except Exception as e:
                    logger.warning("Memory extraction failed", exc_info=e)

            # Auto-consolidate every 10 exchanges
            if exchange_count % 10 == 0:
                try:
                    result = consolidator.auto_consolidate_if_needed(threshold=20)
                    if result:
                        logger.info("Auto-consolidation complete", extra=result.__dict__)
                except Exception as e:
                    logger.warning("Auto-consolidation failed", exc_info=e)

        except Exception as e:
            logger.error("LLM request failed", exc_info=e)
            print(f"\nError: {e}")

            # Remove the unsent user message
            remove_last_message()

    return 0


if __name__ == "__main__":
    sys.exit(main())