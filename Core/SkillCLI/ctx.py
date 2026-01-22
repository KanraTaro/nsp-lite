"""Context helpers for SkillCLI.

The context object supplies skills with a consistent view of the
repository root, node identity and durability helpers.  Instead of
passing many individual parameters through the call chain, a single
object returned from :func:`create_ctx` bundles together the pieces of
state that a skill may need.

The context object currently exposes the following attributes:

``root``
    A :class:`pathlib.Path` pointing at the repository root, resolved via
    :func:`ProjectRoot.get_effective_root`.

``node_tag``
    A string identifying the current node.  Defaults to the value
    provided by :func:`NodeCTX.get_default_node_tag` but may be
    overridden via CLI flags.

``instance_id``
    A string identifying the current instance.  Defaults to
    :func:`NodeCTX.get_default_instance_id` but may be overridden via
    CLI flags.

``global_scope``
    A boolean indicating whether operations should be scoped globally
    (``True``) or per-node (``False``).

``node_ctx``
    A reference to the :mod:`NodeCTX` module for durable writes and
    canonical path routing.  Skills should use methods from this
    reference instead of importing NodeCTX directly.

Additional attributes may be added over time.  Skills should not rely
on private implementation details of the context; instead, they
should treat it as a simple namespace of values and helpers.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Import NodeCTX and ProjectRoot lazily.  These imports rely on the
# bootstrap snippet executed in __main__.py to put Core on sys.path.
# Import NodeCTX and ProjectRoot relative to the Core package.  Using
# fully-qualified names avoids reliance on the bootstrap snippet when
# these modules are imported directly during unit tests.  When run via
# ``python -m Core.SkillCLI`` the bootstrap will add the project root
# to sys.path so these imports continue to work.
from Core.NodeCTX import get_default_instance_id, get_default_node_tag
import Core.NodeCTX as _node_ctx  # import alias for convenience
from Core.ProjectRoot import get_effective_root


@dataclass
class SkillContext:
    """Simple namespace bundling contextual information for skills."""

    root: Path
    node_tag: str
    instance_id: str
    global_scope: bool
    node_ctx: Any
    debug: bool = False
    json: bool = False


def create_ctx(args: argparse.Namespace) -> SkillContext:
    """Construct a :class:`SkillContext` from parsed CLI arguments.

    The ``args`` namespace should contain at least the following
    attributes, which are provided by the SkillCLI argument parser:

    - ``node_tag``: optional override for the node identity
    - ``instance_id``: optional override for the instance identity
    - ``global_scope``: whether to operate in global scope
    - ``debug``: enable verbose debug mode
    - ``json``: request machine-readable output

    Skills may ignore fields they do not need.  Additional values may
    be surfaced on the context as future versions of SkillCLI evolve.
    """

    # Determine the repository root using ProjectRoot.  This call does
    # not write to disk and has no side effects aside from logging.
    root: Path = get_effective_root()

    # Derive node identity parameters, falling back to NodeCTX defaults
    node_tag: str = getattr(args, "node_tag", None) or get_default_node_tag()
    instance_id: str = getattr(args, "instance_id", None) or get_default_instance_id()
    # Global scope is a boolean flag; default is False when not set
    global_scope: bool = bool(getattr(args, "global_scope", False))

    debug: bool = bool(getattr(args, "debug", False))
    json_flag: bool = bool(getattr(args, "json", False))

    # Build and return the context dataclass.  Do not create or write any
    # directories here; path routing is deferred to NodeCTX.
    return SkillContext(
        root=root,
        node_tag=node_tag,
        instance_id=instance_id,
        global_scope=global_scope,
        node_ctx=_node_ctx,
        debug=debug,
        json=json_flag,
    )
