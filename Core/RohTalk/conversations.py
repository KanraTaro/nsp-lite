"""Durable conversation store for RohTalk.

This module implements the persistence layer for RohTalk conversations.
Each conversation is identified by a unique identifier and consists of
metadata stored as JSON and an append-only event log stored as JSONL.

All filesystem interaction goes through ctx.node_ctx, ensuring canonical
routing and durable writes. Reading metadata uses ctx.node_ctx.read_json().
Event logs are append-only and are not read back by the core. Instead,
the conversation metadata contains a canonical copy of the message
history for efficient retrieval.

Conversations live under:

State/<Instance>/<Scope>/RohTalk/Workflow/Conversations/

File naming honours NodeCTX prefixing to allow for provenance when files
leave the local node. The base conversation identifier used by callers
does not include the prefix. Prefix handling is abstracted behind helper
functions in this module.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from Core.LLMClient.client import LLMClient
from Core.LLMClient.types import ChatResult

from .config import load_config
from .messages import append_user_message, assemble_initial_messages


def _conversation_dir(ctx) -> Path:
    """Return the directory where conversations are stored for this context."""
    node_ctx = ctx.node_ctx
    return node_ctx.build_state_dir(
        root=ctx.root,
        instance_id=ctx.instance_id,
        node_tag=ctx.node_tag,
        bucket="Workflow",
        domain="RohTalk",
        global_scope=ctx.global_scope,
        subpath="Conversations",
    )


def _metadata_path(ctx, conversation_id: str) -> Path:
    """Compute the metadata file path for a conversation."""
    node_ctx = ctx.node_ctx
    file_name = f"{conversation_id}.json"
    prefixed = node_ctx.apply_prefix(
        file_name,
        global_scope=ctx.global_scope,
        node_tag=ctx.node_tag,
        instance_id=ctx.instance_id,
    )
    return _conversation_dir(ctx) / prefixed


def _events_path(ctx, conversation_id: str) -> Path:
    """Compute the events log file path for a conversation."""
    node_ctx = ctx.node_ctx
    file_name = f"{conversation_id}.events.jsonl"
    prefixed = node_ctx.apply_prefix(
        file_name,
        global_scope=ctx.global_scope,
        node_tag=ctx.node_tag,
        instance_id=ctx.instance_id,
    )
    return _conversation_dir(ctx) / prefixed


def _iso_now() -> str:
    """Return current UTC time in ISO 8601 format with a trailing Z."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _derive_title(user_message: str, *, max_length: int = 60) -> str:
    """Derive a simple human-readable title from the first user message."""
    cleaned = " ".join(str(user_message).strip().split())
    if cleaned == "":
        return "Untitled Conversation"

    if len(cleaned) <= max_length:
        return cleaned

    trimmed = cleaned[:max_length].rstrip()
    return f"{trimmed}..."


def create_conversation(
    ctx,
    user_message: str,
    *,
    kind: str = "conversation",
    model: Optional[str] = None,
    host: Optional[str] = None,
    title: Optional[str] = None,
    skip_model: bool = False,
) -> Tuple[str, str]:
    """Create a new conversation, persist it and return the id and reply."""
    node_ctx = ctx.node_ctx
    config = load_config(ctx)

    model_to_use = model or config.default_model
    host_to_use = host or config.default_host
    resolved_title = str(title).strip() if title is not None and str(title).strip() != "" else _derive_title(user_message)

    initial_messages = assemble_initial_messages(config.agent_identity, user_message)

    assistant_text = ""
    if not skip_model:
        client = LLMClient()
        result: ChatResult = client.chat(initial_messages, model=model_to_use, host=host_to_use)
        assistant_text = result.text

    conversation_id = uuid.uuid4().hex

    conv_messages: List[Dict[str, Any]] = [
        {"role": "system", "content": config.agent_identity},
        {"role": "user", "content": user_message},
    ]

    if not skip_model:
        conv_messages.append({"role": "assistant", "content": assistant_text})

    now_iso = _iso_now()
    metadata: Dict[str, Any] = {
        "id": conversation_id,
        "title": resolved_title,
        "kind": kind,
        "created_at": now_iso,
        "updated_at": now_iso,
        "messages": conv_messages,
        "model": model_to_use,
        "host": host_to_use,
        "agent_name": config.agent_name,
    }

    conv_dir = _conversation_dir(ctx)
    node_ctx.ensure_dir(conv_dir)

    meta_path = _metadata_path(ctx, conversation_id)
    node_ctx.write_json_atomic(meta_path, metadata)

    events_path = _events_path(ctx, conversation_id)
    for msg in conv_messages:
        event = {
            "timestamp": _iso_now(),
            "role": msg.get("role"),
            "content": msg.get("content"),
        }
        node_ctx.append_jsonl(events_path, event)

    return conversation_id, assistant_text


def get_conversation(ctx, conversation_id: str) -> Dict[str, Any]:
    """Load and return a conversation metadata object by id."""
    node_ctx = ctx.node_ctx
    meta_path = _metadata_path(ctx, conversation_id)

    try:
        metadata = node_ctx.read_json(meta_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Conversation '{conversation_id}' does not exist")

    if not isinstance(metadata, dict):
        raise ValueError(f"Conversation '{conversation_id}' metadata is not a JSON object")

    return metadata


def append_message(
    ctx,
    conversation_id: str,
    user_message: str,
    *,
    model: Optional[str] = None,
    host: Optional[str] = None,
) -> str:
    """Append a user message to an existing conversation and return the reply."""
    node_ctx = ctx.node_ctx
    metadata = get_conversation(ctx, conversation_id)

    messages: List[Dict[str, Any]] = list(metadata.get("messages", []))
    new_messages = append_user_message(messages, user_message)

    config = load_config(ctx)
    model_to_use = model or metadata.get("model") or config.default_model
    host_to_use = host or metadata.get("host") or config.default_host

    client = LLMClient()
    result: ChatResult = client.chat(new_messages, model=model_to_use, host=host_to_use)
    assistant_text = result.text

    messages.append({"role": "user", "content": user_message})
    messages.append({"role": "assistant", "content": assistant_text})

    now_iso = _iso_now()
    metadata["messages"] = messages
    metadata["updated_at"] = now_iso
    metadata["model"] = model_to_use
    metadata["host"] = host_to_use

    meta_path = _metadata_path(ctx, conversation_id)
    node_ctx.write_json_atomic(meta_path, metadata)

    events_path = _events_path(ctx, conversation_id)
    for role, content in [("user", user_message), ("assistant", assistant_text)]:
        event = {
            "timestamp": _iso_now(),
            "role": role,
            "content": content,
        }
        node_ctx.append_jsonl(events_path, event)

    return assistant_text


def _message_signature(message: Dict[str, Any]) -> str:
    import json

    return json.dumps(message, separators=(",", ":"), sort_keys=True)


def _common_prefix_length(
    left: List[Dict[str, Any]],
    right: List[Dict[str, Any]],
) -> int:
    import json

    def sig(m):
        return json.dumps(m, separators=(",", ":"), sort_keys=True)

    limit = min(len(left), len(right))

    for i in range(limit):
        if not isinstance(left[i], dict) or not isinstance(right[i], dict):
            return i
        if sig(left[i]) != sig(right[i]):
            return i

    return limit


def update_conversation_messages(
    ctx,
    conversation_id: str,
    messages: List[Dict[str, Any]],
    *,
    model: Optional[str] = None,
    host: Optional[str] = None,
) -> None:
    """Persist an updated full message list back into an existing conversation.

    This updates metadata in place and appends only newly-added messages
    to the append-only event log.
    """
    node_ctx = ctx.node_ctx
    metadata = get_conversation(ctx, conversation_id)

    existing_messages = metadata.get("messages", [])
    if not isinstance(existing_messages, list):
        existing_messages = []

    incoming_messages = [
        msg for msg in list(messages)
        if isinstance(msg, dict)
    ]

    current_messages = [
        msg for msg in existing_messages
        if isinstance(msg, dict)
    ]

    prefix_len = _common_prefix_length(current_messages, incoming_messages)

    merged_messages = list(current_messages)
    merged_messages.extend(incoming_messages[prefix_len:])

    metadata["messages"] = merged_messages
    metadata["updated_at"] = _iso_now()

    if model is not None:
        metadata["model"] = model
    if host is not None:
        metadata["host"] = host

    meta_path = _metadata_path(ctx, conversation_id)
    node_ctx.write_json_atomic(meta_path, metadata)

    events_path = _events_path(ctx, conversation_id)
    start_index = len(existing_messages)

    for msg in metadata["messages"][start_index:]:
        if not isinstance(msg, dict):
            continue

        event = {
            "timestamp": _iso_now(),
            "role": msg.get("role"),
            "content": msg.get("content"),
        }
        node_ctx.append_jsonl(events_path, event)
        

def append_note(
    ctx,
    conversation_id: str,
    note_text: str,
    *,
    prefix: str = "[human note]",
) -> None:
    """Append a human note to a conversation without running the model."""
    cleaned = str(note_text).strip()
    if cleaned == "":
        raise ValueError("Note text cannot be empty.")

    metadata = get_conversation(ctx, conversation_id)
    messages = metadata.get("messages", [])
    if not isinstance(messages, list):
        messages = []

    content = f"{prefix} {cleaned}"
    messages.append({"role": "user", "content": content})

    update_conversation_messages(ctx, conversation_id, messages)


def list_conversations(
    ctx,
    *,
    include_oneshots: bool = False,
) -> List[Dict[str, Any]]:
    """Return a list of conversation metadata dictionaries."""
    node_ctx = ctx.node_ctx
    conv_dir = _conversation_dir(ctx)
    result: List[Dict[str, Any]] = []

    if not node_ctx.exists(conv_dir):
        return result

    global_tag = node_ctx.get_default_global_tag()

    for entry in node_ctx.list_dir(conv_dir):
        if not node_ctx.is_file(entry):
            continue

        if entry.suffix != ".json":
            continue

        base_name = node_ctx.strip_prefix_base_name(
            entry.name,
            node_tag=ctx.node_tag,
            global_tag=global_tag,
            instance_id=ctx.instance_id,
        )

        if not base_name.endswith(".json"):
            continue

        try:
            meta = node_ctx.read_json(entry)
        except Exception:
            continue

        if not isinstance(meta, dict):
            continue

        if "title" not in meta or str(meta.get("title", "")).strip() == "":
            messages = meta.get("messages", [])
            if isinstance(messages, list) and len(messages) > 1:
                first_user = messages[1].get("content", "") if isinstance(messages[1], dict) else ""
                meta["title"] = _derive_title(str(first_user))
            else:
                meta["title"] = f"Conversation {str(meta.get('id', 'unknown'))[:8]}"

        if not include_oneshots and meta.get("kind") == "oneshot":
            continue

        result.append(meta)

    def _sort_key(item: Dict[str, Any]) -> str:
        return str(item.get("updated_at") or item.get("created_at") or "")

    result.sort(key=_sort_key)
    return result
