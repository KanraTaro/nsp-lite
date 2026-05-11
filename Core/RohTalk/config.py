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
* ``default_options`` - optional provider request options such as
  Ollama's top-level ``think`` control.
* ``profiles`` - optional named model profiles with ``model``, ``host``,
  and ``options`` fields.

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

import json
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
    default_options: Dict[str, Any] | None = None
    profiles: Dict[str, Dict[str, Any]] | None = None


@dataclass(frozen=True)
class ResolvedModelProfile:
    """Resolved model runtime settings for a RohTalk model call."""

    profile_name: str | None
    model: str
    host: str | None
    options: Dict[str, Any]


_DEFAULTS: Dict[str, Any] = {
    "agent_name": "Roh",
    "agent_identity": (
        "You are Roh, a succinct and helpful assistant. "
        "Answer the user's questions clearly and concisely."
    ),
    "default_model": "qwen3:0.6b",
    "default_host": None,
    "default_options": {},
    "profiles": {},
}


def _clean_options(value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {str(key): item for key, item in value.items() if str(key).strip() != ""}


def _clean_profiles(value: Any) -> Dict[str, Dict[str, Any]]:
    if not isinstance(value, dict):
        return {}

    profiles: Dict[str, Dict[str, Any]] = {}
    for raw_name, raw_profile in value.items():
        name = str(raw_name or "").strip()
        if name == "" or not isinstance(raw_profile, dict):
            continue

        profile: Dict[str, Any] = {}
        if raw_profile.get("model") is not None:
            profile["model"] = str(raw_profile.get("model"))
        if raw_profile.get("host") is not None:
            profile["host"] = str(raw_profile.get("host"))
        profile["options"] = _clean_options(raw_profile.get("options", {}))
        profiles[name] = profile

    return profiles


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
        default_options=_clean_options(merged.get("default_options", {})),
        profiles=_clean_profiles(merged.get("profiles", {})),
    )


def parse_model_option_args(values: Any) -> Dict[str, Any]:
    """Parse repeated key=value CLI options into a model options dict."""
    options: Dict[str, Any] = {}
    for raw_value in list(values or []):
        text = str(raw_value or "").strip()
        if text == "":
            continue
        if "=" not in text:
            raise ValueError(f"Model option must be key=value: {text}")
        key, raw_option_value = text.split("=", 1)
        key = key.strip()
        if key == "":
            raise ValueError(f"Model option key cannot be empty: {text}")

        raw_option_value = raw_option_value.strip()
        try:
            parsed_value = json.loads(raw_option_value)
        except json.JSONDecodeError:
            lowered = raw_option_value.lower()
            if lowered == "true":
                parsed_value = True
            elif lowered == "false":
                parsed_value = False
            elif lowered == "null":
                parsed_value = None
            else:
                parsed_value = raw_option_value
        options[key] = parsed_value
    return options


def resolve_model_profile(
    ctx: Any,
    profile_name: str | None = None,
    *,
    model_override: str | None = None,
    host_override: str | None = None,
    option_overrides: Dict[str, Any] | None = None,
) -> ResolvedModelProfile:
    """Resolve model, host, and options from config, profile, and overrides."""
    config = load_config(ctx)
    selected_profile_name = str(profile_name or "").strip() or None
    profiles = config.profiles or {}

    profile: Dict[str, Any] = {}
    if selected_profile_name is not None:
        profile = profiles.get(selected_profile_name, {})
        if not profile:
            raise ValueError(f"Unknown RohTalk model profile: {selected_profile_name}")

    options: Dict[str, Any] = dict(config.default_options or {})
    options.update(_clean_options(profile.get("options", {})))
    options.update(_clean_options(option_overrides or {}))

    model = str(
        model_override
        or profile.get("model")
        or config.default_model
    )
    host = host_override
    if host is None:
        host = profile.get("host") or config.default_host

    return ResolvedModelProfile(
        profile_name=selected_profile_name,
        model=model,
        host=host,
        options=options,
    )
