"""
Session state management implementation.

Provides thread-safe session state storage using FastAPI's app.state.
"""

import threading
from typing import Any, Dict, Optional, Union

from devleaps.policies.server.server import app
from devleaps.policies.server.common.models import BaseEvent


# Thread lock for session state access
_state_lock = threading.Lock()


def initialize_session_state():
    """
    Initialize the session state storage in app.state.

    Should be called once at server startup before any policies are registered.
    """
    if not hasattr(app.state, "sessions"):
        app.state.sessions = {}


def get_session_state(event: BaseEvent) -> Dict[str, Any]:
    """
    Get the full state dictionary for a session.

    Creates an empty state dict if the session doesn't exist.

    Args:
        event: The event containing session_id

    Returns:
        Dictionary containing all state for this session
    """
    session_id = event.session_id

    with _state_lock:
        if not hasattr(app.state, "sessions"):
            initialize_session_state()

        if session_id not in app.state.sessions:
            app.state.sessions[session_id] = {}

        return app.state.sessions[session_id].copy()


def set_session_flag(event: BaseEvent, key: str, value: Any) -> None:
    """
    Set a state flag/value for a session.

    Args:
        event: The event containing session_id
        key: The state key to set
        value: The value to store (can be any JSON-serializable type)
    """
    session_id = event.session_id

    with _state_lock:
        if not hasattr(app.state, "sessions"):
            initialize_session_state()

        if session_id not in app.state.sessions:
            app.state.sessions[session_id] = {}

        app.state.sessions[session_id][key] = value


def get_session_flag(event: BaseEvent, key: str, default: Any = None) -> Any:
    """
    Get a state flag/value for a session.

    Args:
        event: The event containing session_id
        key: The state key to get
        default: Default value if key doesn't exist

    Returns:
        The value stored for this key, or default if not found
    """
    session_id = event.session_id

    with _state_lock:
        if not hasattr(app.state, "sessions"):
            initialize_session_state()

        if session_id not in app.state.sessions:
            return default

        return app.state.sessions[session_id].get(key, default)


def clear_session_state(event: BaseEvent) -> None:
    """
    Clear all state for a session.

    Args:
        event: The event containing session_id to clear
    """
    session_id = event.session_id

    with _state_lock:
        if not hasattr(app.state, "sessions"):
            initialize_session_state()

        if session_id in app.state.sessions:
            del app.state.sessions[session_id]


def list_sessions() -> list[str]:
    """
    List all active session IDs.

    Returns:
        List of session IDs that have state stored
    """
    with _state_lock:
        if not hasattr(app.state, "sessions"):
            initialize_session_state()

        return list(app.state.sessions.keys())
