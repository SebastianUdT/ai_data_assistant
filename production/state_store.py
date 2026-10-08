"""
Durable Run-State Storage

PURPOSE
-------
Store paused OpenAI Agents SDK RunState snapshots.

REFERENCE ARCHITECTURE
----------------------

Agent pauses
    ↓
RunState
    ↓
StateStore
    ↓
Persistent storage

Later:

Persistent storage
    ↓
StateStore
    ↓
RunState
    ↓
approve/reject
    ↓
Runner resumes


CURRENT IMPLEMENTATION
----------------------
We use JSON files.

This is intentionally simple.

PRODUCTION
----------
A real application would normally use something like:

- PostgreSQL
- durable workflow storage
- job database
- Redis + durable backing store
- another trusted server-side persistence system


SECURITY
--------
Serialized RunState is TRUSTED SERVER STATE.

Never accept a serialized RunState directly from a browser or client
and resume it without verifying its integrity and ownership.

The client should normally receive only:

- opaque run/request ID
- safe operation description
- safe arguments needed for review

The full state remains server-side.
"""

import json
from pathlib import Path
from typing import Any


# =====================================================================
# STORAGE LOCATION
# =====================================================================


STATE_DIRECTORY = (
    Path(__file__).parent
    / "pending_runs"
)


def _state_path(
    run_id: str,
) -> Path:
    """
    Return the JSON file used for one pending run.
    """

    return (
        STATE_DIRECTORY
        / f"{run_id}.json"
    )


# =====================================================================
# SAVE
# =====================================================================


def save_state(
    run_id: str,
    state_json: dict[str, Any],
) -> Path:
    """
    Persist serialized RunState.

    IMPORTANT:
    This storage is application-controlled.

    The approval client should never be allowed to replace this
    snapshot with arbitrary JSON.
    """

    STATE_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = _state_path(run_id)

    path.write_text(
        json.dumps(
            state_json,
            indent=2,
        ),
        encoding="utf-8",
    )

    return path


# =====================================================================
# LOAD
# =====================================================================


def load_state(
    run_id: str,
) -> dict[str, Any]:
    """
    Load a trusted server-owned RunState snapshot.
    """

    path = _state_path(run_id)

    if not path.exists():
        raise FileNotFoundError(
            f"Pending run not found: {run_id}"
        )

    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


# =====================================================================
# DELETE
# =====================================================================


def delete_state(
    run_id: str,
) -> None:
    """
    Remove a pending run after it has been consumed.

    PRODUCTION
    ----------
    Real systems need stronger lifecycle handling:

    - atomic state transitions
    - replay protection
    - audit history
    - expiration
    - recovery
    - concurrency protection
    """

    path = _state_path(run_id)

    if path.exists():
        path.unlink()