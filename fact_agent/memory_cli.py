#!/usr/bin/env python3
"""CLI for managing Fact Agent memory."""

import sys
import argparse
import sqlite3
from pathlib import Path

from .config import get_settings
from .memory_retriever import retrieve_memories
from .memory_extractor import extract_and_store
from .memory_consolidator import MemoryConsolidator, MemoryJanitor
from .http_client import LLMClient
from .logging_setup import setup_logging


settings = get_settings()
setup_logging(settings)


def cmd_list(args):
    """List all long-term memories."""
    db_path = settings.long_term_memory_db_path
    with sqlite3.connect(db_path) as db:
        rows = db.execute("SELECT id, category, fact, created_at FROM memories ORDER BY id").fetchall()

    if not rows:
        print("No memories stored.")
        return

    print(f"Found {len(rows)} memories:\n")
    for id_, category, fact, created in rows:
        print(f"  [{id_}] {category}: {fact}")
        print(f"      Created: {created}\n")


def cmd_search(args):
    """Search memories by keyword."""
    db_path = settings.long_term_memory_db_path
    client = LLMClient(
        api_url=settings.llm_api_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
    ) if settings.enable_semantic_retrieval else None

    result = retrieve_memories(
        query=args.query,
        limit=args.limit,
        client=client,
    )

    if result:
        print(result)
    else:
        print("No matching memories found.")


def cmd_extract(args):
    """Extract and store memories from text."""
    client = LLMClient(
        api_url=settings.llm_api_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
    )

    count = extract_and_store(args.text, client)
    print(f"Extracted and stored {count} memories.")


def cmd_stats(args):
    """Show memory statistics."""
    # Short-term
    with sqlite3.connect(settings.memory_db_path) as db:
        conv_count = db.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]

    # Long-term
    with sqlite3.connect(settings.long_term_memory_db_path) as db:
        mem_count = db.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        cats = db.execute("SELECT category, COUNT(*) FROM memories GROUP BY category").fetchall()

    print(f"Short-term conversations: {conv_count}")
    print(f"Long-term memories: {mem_count}")
    if cats:
        print("By category:")
        for cat, count in cats:
            print(f"  {cat}: {count}")


def cmd_clear(args):
    """Clear memories (with confirmation)."""
    if not args.yes:
        confirm = input("This will delete ALL memories. Type 'YES' to confirm: ")
        if confirm != "YES":
            print("Cancelled.")
            return

    with sqlite3.connect(settings.memory_db_path) as db:
        db.execute("DELETE FROM conversations")
        db.commit()

    with sqlite3.connect(settings.long_term_memory_db_path) as db:
        db.execute("DELETE FROM memories")
        db.commit()

    print("All memories cleared.")


def cmd_consolidate(args):
    """Run memory consolidation."""
    client = LLMClient(
        api_url=settings.llm_api_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
    )
    consolidator = MemoryConsolidator(client=client)
    result = consolidator.consolidate(max_messages=args.max, min_messages=args.min)

    if result:
        print(f"Consolidation complete:")
        print(f"  Messages processed: {result.messages_processed}")
        print(f"  Key facts extracted: {result.key_facts_extracted}")
        print(f"  Decisions recorded: {result.decisions_recorded}")
        print(f"  Memories stored: {result.memories_stored}")
        if result.summary:
            print(f"  Summary: {result.summary}")
    else:
        print("No consolidation needed (insufficient messages)")


def cmd_cleanup(args):
    """Run TTL-based memory cleanup."""
    janitor = MemoryJanitor()
    result = janitor.run_all_cleanup()
    print(f"Cleanup complete:")
    print(f"  Conversations deleted: {result['conversations_deleted']}")
    print(f"  Long-term memories deleted: {result['long_term_deleted']}")


def cmd_categories(args):
    """List available memory categories."""
    from .memory_consolidator import get_categories
    categories = get_categories()
    print("Available memory categories:")
    for cat in categories:
        print(f"  {cat}")


def main():
    parser = argparse.ArgumentParser(description="Fact Agent Memory CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list
    subparsers.add_parser("list", help="List all long-term memories")

    # search
    search = subparsers.add_parser("search", help="Search memories")
    search.add_argument("query", help="Search query")
    search.add_argument("-l", "--limit", type=int, default=8, help="Max results")

    # extract
    extract = subparsers.add_parser("extract", help="Extract memories from text")
    extract.add_argument("text", help="Text to extract memories from")

    # stats
    subparsers.add_parser("stats", help="Show memory statistics")

    # clear
    clear = subparsers.add_parser("clear", help="Clear all memories")
    clear.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")

    # consolidate
    consol = subparsers.add_parser("consolidate", help="Run memory consolidation")
    consol.add_argument("--max", type=int, default=50, help="Max messages to process")
    consol.add_argument("--min", type=int, default=10, help="Min messages required")

    # cleanup
    cleanup = subparsers.add_parser("cleanup", help="Run TTL-based cleanup")

    # categories
    subparsers.add_parser("categories", help="List available memory categories")

    args = parser.parse_args()

    commands = {
        "list": cmd_list,
        "search": cmd_search,
        "extract": cmd_extract,
        "stats": cmd_stats,
        "clear": cmd_clear,
        "consolidate": cmd_consolidate,
        "cleanup": cmd_cleanup,
        "categories": cmd_categories,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()