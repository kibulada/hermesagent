#!/usr/bin/env python3
"""
ai_pending.py — Track pending AI test generation requests.
Simple JSON-based state management untuk AI request/response flow.
"""
import json
import time
from pathlib import Path
from typing import Optional

STATE_FILE = Path(__file__).parent.parent / 'temp' / 'ai-pending.json'


def load_state() -> dict:
    """Load pending requests state from JSON file."""
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(state: dict) -> None:
    """Save pending requests state to JSON file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding='utf-8')


def register_pending(ticket_id: int, thread_id: str, request_msg_id: str, slug: str) -> None:
    """
    Track pending AI request.
    
    Args:
        ticket_id: OpenProject work package ID
        thread_id: Discord thread/channel ID
        request_msg_id: Discord message ID of AI request
        slug: Slugified ticket subject for spec filename
    """
    state = load_state()
    state[str(ticket_id)] = {
        'thread_id': thread_id,
        'request_msg_id': request_msg_id,
        'slug': slug,
        'timestamp': time.time()
    }
    save_state(state)


def get_pending(ticket_id: int) -> Optional[dict]:
    """
    Get pending request for ticket.
    
    Returns:
        dict with thread_id, request_msg_id, slug, timestamp or None
    """
    state = load_state()
    return state.get(str(ticket_id))


def clear_pending(ticket_id: int) -> None:
    """Clear pending request after AI responds."""
    state = load_state()
    state.pop(str(ticket_id), None)
    save_state(state)


def get_all_pending() -> dict:
    """Get all pending requests (for message listener)."""
    return load_state()
