"""RohTalk configuration utilities.

This module defines a minimal configuration surface for the RohTalk
system. Configuration values are loaded from disk via ctx.node_ctx,
falling back to repository defaults when no user overrides are
present.

The configuration controls:

* ``agent_name`` - a human friendly identifier for the agent. This is
  recorded in conversation metadata but is not sent to the model.
* ``agent_identity`` - a system prompt injected as the very first
  message in every conversation. It should clearly describe the
  assistant's role and behaviour.
* ``default_model`` - the identifier of the model to use when none is
  supplied on the command line. Use ``qwen3:0.6b`` for examples.
* ``default_host`` - optional base URL of the model backend. When
  omitted, the underlying LLMClient will use its own default.

The lookup order for configuration values is:

1. ``State/<Instance>/<Scope>/RohTalk/Config/config.json``
2. ``Config/RohTalk/config.json`` under the repository root
3. Hard-coded defaults in this module

Files must contain a JSON object. Unknown keys are ignored. Missing
keys fall back to hard-coded defaults.

The returned configuration is represented by the dataclass
``RohTalkConfig`` for convenience. Fields are read-only and safe to
inspect. ``load_config()`` accepts a ``SkillContext`` and returns
the resolved configuration.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass(frozen=True)
class RohTalkConfig:
    """Concrete configuration values for RohTalk."""

    agent_name: str
    agent_identity: str
    default_model: str
    default_host: str | None = None


_DEFAULTS: Dict[str, Any] = {
    "agent_name": "Roh",
    "agent_identity": (
        "You are Roh, a succinct and helpful assistant. "
        "Answer the user's questions clearly and concisely."
    ),
    "default_model": "qwen3:1.7b",
    "default_host": None,
}


def _load_config_file(ctx, path: Path) -> Dict[str, Any]:
    """Attempt to load a JSON config file via ctx.node_ctx.

    If the file does not exist, returns an empty dict.
    If the file exists but does not contain a JSON object, returns an empty dict.
    Unexpected exceptions are propagated.
    """
    node_ctx = ctx.node_ctx

    try:
        data = node_ctx.read_json(path)
        if not isinstance(data, dict):
            return {}
        return data
    except FileNotFoundError:
        return {}


def load_config(ctx) -> RohTalkConfig:
    """Resolve the RohTalk configuration for the provided context."""
    node_ctx = ctx.node_ctx
    merged: Dict[str, Any] = dict(_DEFAULTS)

    state_config_dir = node_ctx.build_state_dir(
        root=ctx.root,
        instance_id=ctx.instance_id,
        node_tag=ctx.node_tag,
        bucket="Config",
        domain="RohTalk",
        global_scope=ctx.global_scope,
    )
    state_config_path = state_config_dir / "config.json"
    state_data = _load_config_file(ctx, state_config_path)
    merged.update({key: value for key, value in state_data.items() if key in _DEFAULTS})

    repo_config_path = Path(ctx.root) / "Config" / "RohTalk" / "config.json"
    repo_data = _load_config_file(ctx, repo_config_path)
    merged.update({key: value for key, value in repo_data.items() if key in _DEFAULTS})

    return RohTalkConfig(
        agent_name=merged["agent_name"],
        agent_identity=merged["agent_identity"],
        default_model=merged["default_model"],
        default_host=merged.get("default_host"),
    )
