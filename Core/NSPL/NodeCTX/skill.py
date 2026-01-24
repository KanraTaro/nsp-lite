"""Node context routing and durable I/O helpers.

NodeCTX is responsible for constructing canonical storage paths under
``State/``, performing durable JSON/text/binary writes, and prefixing
filenames for provenance. It does not know how to locate the ``State/``
directory itself-that responsibility is delegated to RuntimeRoot-and it
never hardcodes project names or paths.

Environment variables can be used to override identity defaults and
prefixing behaviour. Refer to the module-level functions:

- get_default_node_tag()
- get_default_instance_id()
- get_default_global_tag()
- is_prefix_enabled()
- is_prefix_instance()

for details.
"""

from __future__ import annotations

import json
import logging
import os
import re
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Union, Dict, Any

logger = logging.getLogger(__name__)

# ---- Metadata ---------------------------------------------------------------

__nsp_module_name__ = "NodeCTX"
__nsp_module_version__ = "1.0.0"


# ---- Internal helpers --------------------------------------------------------

_TRUE_WORDS = {"1", "true", "yes", "y", "on"}
_FALSE_WORDS = {"0", "false", "no", "n", "off", ""}


def _parse_env_bool(value: Optional[str], *, default: bool) -> bool:
    """Parse a human-friendly boolean from env strings.

    True:  1/true/yes/y/on
    False: 0/false/no/n/off/"" (empty)
    Unset/unknown: default
    """
    if value is None:
        return default

    cleaned = value.strip().casefold()
    if cleaned in _TRUE_WORDS:
        return True
    if cleaned in _FALSE_WORDS:
        return False
    return default


def _validate_segment(name: str, value: str) -> str:
    """Validate a path segment used in canonical routing.

    Disallows:
    - empty/whitespace
    - path separators
    - "." or ".." segments (to prevent traversal)
    """
    if value is None:
        raise ValueError(f"{name} must be a non-empty string")

    text = str(value).strip()
    if not text:
        raise ValueError(f"{name} must be a non-empty string")

    # Reject path separators on all platforms (Windows has altsep='/').
    altsep: Optional[str] = os.path.altsep
    if "/" in text or os.path.sep in text or (altsep is not None and altsep in text):
        raise ValueError(f"{name} must be a simple folder name, not a path")

    # Prevent traversal / weirdness.
    if text in {".", ".."}:
        raise ValueError(f"{name} must not be '.' or '..'")

    # Extra Windows hardening: ':' can be problematic (drive/ADS).
    if os.name == "nt" and ":" in text:
        raise ValueError(f"{name} must not contain ':' on Windows")

    return text

# ---- Defaults / identity -----------------------------------------------------

def get_default_node_tag() -> str:
    """Return the default node identifier.

    Default order:
    1) NODECTX_NODE_TAG env var
    2) hostname
    3) "default"
    """
    env_tag = os.environ.get("NODECTX_NODE_TAG")
    if env_tag:
        return env_tag

    try:
        host = os.uname().nodename
    except AttributeError:
        import platform
        host = platform.node()

    host = host or "default"
    return host


def get_default_instance_id() -> str:
    """Return the default instance identifier (defaults to "main")."""
    return os.environ.get("NODECTX_INSTANCE_ID", "main")


def get_default_global_tag() -> str:
    """Return the default tag used for global-scope prefixing.

    Default is "Global" unless overridden by NODECTX_GLOBAL_TAG.
    """
    return os.environ.get("NODECTX_GLOBAL_TAG", "Global")


def is_prefix_enabled() -> bool:
    """Return whether filename prefixing is enabled.

    Controlled by NODECTX_ENABLE_PREFIXING.
    Default: enabled
    """
    return _parse_env_bool(os.environ.get("NODECTX_ENABLE_PREFIXING"), default=True)


def is_prefix_instance() -> bool:
    """Return whether instance prefixes should be included in file names.

    Controlled by NODECTX_PREFIX_INSTANCE.
    Default: disabled
    """
    return _parse_env_bool(os.environ.get("NODECTX_PREFIX_INSTANCE"), default=False)

# ---- Prefixing ---------------------------------------------------------------

def apply_prefix(
    file_name: str,
    *,
    global_scope: bool = False,
    node_tag: Optional[str] = None,
    instance_id: Optional[str] = None,
    global_tag: Optional[str] = None,
    enable_prefixing: Optional[bool] = None,
    prefix_instance: Optional[bool] = None,
) -> str:
    """Return a filename with provenance prefixes applied.

    Format when enabled:
      <node_or_global>-<file_name>
    Or (optionally):
      <instance>-<node_or_global>-<file_name>

    NOTE: Prefixing is provenance-only. Folder routing remains canonical.
    """
    if not file_name:
        raise ValueError("apply_prefix expects a non-empty base filename")

    altsep: Optional[str] = os.path.altsep
    if "/" in file_name or os.path.sep in file_name or (altsep is not None and altsep in file_name):
        raise ValueError("apply_prefix expects a base filename, not a path")
      
    if os.name == "nt" and ":" in file_name:
        raise ValueError("apply_prefix expects a base filename, not a drive/ADS path")

    if enable_prefixing is None:
        enable_prefixing = is_prefix_enabled()
    if not enable_prefixing:
        return file_name

    if prefix_instance is None:
        prefix_instance = is_prefix_instance()

    if instance_id is None:
        instance_id = get_default_instance_id()
    if node_tag is None:
        node_tag = get_default_node_tag()
    if global_tag is None:
        global_tag = get_default_global_tag()

    parts: List[str] = []
    if prefix_instance:
        parts.append(instance_id)
    parts.append(global_tag if global_scope else node_tag)

    prefix = "-".join(parts)
    return f"{prefix}-{file_name}"


def strip_prefix(
    file_name: str,
    *,
    node_tag: Optional[str] = None,
    global_tag: Optional[str] = None,
    instance_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Attempt to strip known NodeCTX prefixes from a filename.

    Supports these patterns:
    - <node>-<name>
    - <global>-<name>
    - <instance>-<node>-<name>
    - <instance>-<global>-<name>

    Returns a dict with:
      - original
      - base_name
      - had_prefix
      - had_instance_prefix
      - prefix_tag (node/global tag used, if any)
      - instance_id (if parsed)
      - global_scope (True if global tag matched)
    """
    if node_tag is None:
        node_tag = get_default_node_tag()
    if global_tag is None:
        global_tag = get_default_global_tag()
    if instance_id is None:
        instance_id = get_default_instance_id()

    original = file_name

    def _try_strip(prefix: str, text: str) -> Optional[str]:
        if text.startswith(prefix):
            return text[len(prefix):]
        return None

    # Try instance + node/global first (more specific).
    inst_node_prefix = f"{instance_id}-{node_tag}-"
    inst_global_prefix = f"{instance_id}-{global_tag}-"
    stripped = _try_strip(inst_node_prefix, file_name)
    if stripped is not None:
        return {
            "original": original,
            "base_name": stripped,
            "had_prefix": True,
            "had_instance_prefix": True,
            "prefix_tag": node_tag,
            "instance_id": instance_id,
            "global_scope": False,
        }

    stripped = _try_strip(inst_global_prefix, file_name)
    if stripped is not None:
        return {
            "original": original,
            "base_name": stripped,
            "had_prefix": True,
            "had_instance_prefix": True,
            "prefix_tag": global_tag,
            "instance_id": instance_id,
            "global_scope": True,
        }

    # Try node/global only.
    node_prefix = f"{node_tag}-"
    global_prefix = f"{global_tag}-"

    stripped = _try_strip(node_prefix, file_name)
    if stripped is not None:
        return {
            "original": original,
            "base_name": stripped,
            "had_prefix": True,
            "had_instance_prefix": False,
            "prefix_tag": node_tag,
            "instance_id": None,
            "global_scope": False,
        }

    stripped = _try_strip(global_prefix, file_name)
    if stripped is not None:
        return {
            "original": original,
            "base_name": stripped,
            "had_prefix": True,
            "had_instance_prefix": False,
            "prefix_tag": global_tag,
            "instance_id": None,
            "global_scope": True,
        }

    # No match
    return {
        "original": original,
        "base_name": original,
        "had_prefix": False,
        "had_instance_prefix": False,
        "prefix_tag": None,
        "instance_id": None,
        "global_scope": False,
    }


def strip_prefix_base_name(
    file_name: str,
    *,
    node_tag: Optional[str] = None,
    global_tag: Optional[str] = None,
    instance_id: Optional[str] = None,
) -> str:
    """Convenience: return only the base filename with known prefixes removed."""
    return str(strip_prefix(file_name, node_tag=node_tag, global_tag=global_tag, instance_id=instance_id)["base_name"])


# ---- Routing -----------------------------------------------------------------

_CANONICAL_BUCKETS: Dict[str, str] = {
    "config": "Config",
    "data": "Data",
    "workflow": "Workflow",
    "logs": "Logs",
    "sessions": "Sessions",
    "reflections": "Reflections",
    "oneshots": "OneShots",
}

def normalize_bucket(bucket: str) -> str:
    """Normalize bucket casing to avoid path fragmentation.

    If bucket matches a known canonical bucket (case-insensitive), return the canonical casing.
    Otherwise return bucket stripped of surrounding whitespace (custom buckets allowed).
    """
    if not bucket or not bucket.strip():
        raise ValueError("bucket must be a non-empty string")

    b = bucket.strip()

    # Disallow buckets that look like paths.
    if "/" in b or os.path.sep in b:
        raise ValueError("bucket must be a simple folder name, not a path")

    key = b.casefold()
    return _CANONICAL_BUCKETS.get(key, b)


def build_state_dir(
    root: Path,
    instance_id: str,
    node_tag: str,
    bucket: str,
    domain: str,
    *,
    global_scope: bool = False,
    subpath: Optional[Union[str, Sequence[str]]] = None,
) -> Path:
    """Construct a canonical state directory path.

    Canonical layout:
      <root>/State/<InstanceId>/<Scope>/<Bucket>/<Domain>/<Subpath...>/

    Scope is "Global" when global_scope=True, otherwise node_tag.

    The returned path is not created on disk.
    """
    instance_id_clean = _validate_segment("instance_id", instance_id)
    node_tag_clean = _validate_segment("node_tag", node_tag)
    domain_clean = _validate_segment("domain", domain)

    canonical_bucket = normalize_bucket(bucket)

    scope_folder = "Global" if global_scope else node_tag_clean
    path = Path(root) / "State" / instance_id_clean / scope_folder / canonical_bucket / domain_clean

    if subpath:
        if isinstance(subpath, (str, bytes)):
            # Accept both Unix "/" and Windows "\" separators, regardless of platform.
            subpath_text: str = str(subpath)
            raw_parts: List[str] = [p for p in re.split(r"[\\/]+", subpath_text) if p]
        else:
            raw_parts = [str(p) for p in subpath if p]

        for part in raw_parts:
            clean_part = _validate_segment("subpath", part)
            path = path / clean_part

    return path
    

# ---- Durable I/O -------------------------------------------------------------

# ---- JSONL rotation/throttle policy -----------------------------------------

@dataclass(frozen=True)
class JsonlRotationPolicy:
    """Policy for JSONL log rotation."""
    max_bytes: int = 256_000
    keep: int = 5


@dataclass(frozen=True)
class JsonlThrottlePolicy:
    """In-process throttling to reduce spam in tight loops.

    NOTE: This is not persisted. It only limits spam within the current process.
    """
    min_interval_sec: float = 0.0


_JSONL_THROTTLE_LAST_TS: Dict[str, float] = {}


def _now_monotonic() -> float:
    return time.monotonic()


def _should_throttle(throttle_key: str, throttle: JsonlThrottlePolicy) -> bool:
    if throttle.min_interval_sec <= 0.0:
        return False

    now: float = _now_monotonic()
    last: float = _JSONL_THROTTLE_LAST_TS.get(throttle_key, 0.0)
    if last <= 0.0:
        _JSONL_THROTTLE_LAST_TS[throttle_key] = now
        return False

    if (now - last) >= throttle.min_interval_sec:
        _JSONL_THROTTLE_LAST_TS[throttle_key] = now
        return False

    return True


def _rotate_jsonl(path: Path, rotation: JsonlRotationPolicy) -> None:
    """Rotate a JSONL file when it exceeds rotation.max_bytes.

    Layout:
      <name>.jsonl
      <name>.jsonl.1
      <name>.jsonl.2
      ...
    """
    if rotation.max_bytes <= 0:
        return

    keep: int = int(rotation.keep)
    if keep < 1:
        keep = 1

    p: Path = Path(path)
    if not p.exists():
        return

    try:
        size: int = int(p.stat().st_size)
    except Exception:
        return

    if size < int(rotation.max_bytes):
        return

    p.parent.mkdir(parents=True, exist_ok=True)

    # Drop the oldest
    oldest: Path = p.with_name(f"{p.name}.{keep}")
    if oldest.exists():
        try:
            oldest.unlink()
        except Exception:
            pass

    # Shift: .(keep-1) -> .keep, ... .1 -> .2
    for i in range(keep - 1, 0, -1):
        src: Path = p.with_name(f"{p.name}.{i}")
        dst: Path = p.with_name(f"{p.name}.{i + 1}")
        if src.exists():
            try:
                os.replace(str(src), str(dst))
            except Exception:
                pass

    # Current -> .1
    rotated: Path = p.with_name(f"{p.name}.1")
    try:
        os.replace(str(p), str(rotated))
    except Exception:
        pass


def append_jsonl_rotating(
    path: Path,
    obj: object,
    *,
    rotation: Optional[JsonlRotationPolicy] = None,
    throttle_key: Optional[str] = None,
    throttle: Optional[JsonlThrottlePolicy] = None,
) -> None:
    """Append one JSONL line with optional rotation + throttling.

    - Rotation happens BEFORE append.
    - Throttling is in-process only.
    - Uses existing append_jsonl() for durability.
    """
    p: Path = Path(path)

    if throttle_key is not None and throttle is not None:
        if _should_throttle(throttle_key, throttle):
            return

    if rotation is not None:
        _rotate_jsonl(p, rotation)

    append_jsonl(p, obj)


def log_event_jsonl(
    path: Path,
    *,
    kind: str,
    base: Dict[str, Any],
    extra: Optional[Dict[str, Any]] = None,
    rotation: Optional[JsonlRotationPolicy] = None,
    throttle: Optional[JsonlThrottlePolicy] = None,
    throttle_key: Optional[str] = None,
) -> None:
    """Standard event logger for worker/daemon style systems."""
    payload: Dict[str, Any] = dict(base)
    payload["kind"] = str(kind)

    if extra:
        payload.update(extra)

    resolved_key: Optional[str] = throttle_key
    if resolved_key is None and throttle is not None and throttle.min_interval_sec > 0.0:
        resolved_key = f"{str(Path(path))}::{kind}"

    append_jsonl_rotating(
        path=Path(path),
        obj=payload,
        rotation=rotation,
        throttle_key=resolved_key,
        throttle=throttle,
    )

def _fsync_dir(directory: Path) -> None:
    """Best-effort fsync() on a directory to persist rename/metadata updates.

    On platforms without os.O_DIRECTORY (notably Windows), this is a no-op.
    """
    if not hasattr(os, "O_DIRECTORY"):
        return

    try:
        directory_path = Path(directory)
        fd = os.open(str(directory_path), os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except Exception:
        # Not all platforms/filesystems support directory fsync.
        pass


def _atomic_write_bytes(target: Path, data: bytes) -> None:
    """Write bytes to target atomically AND durably.

    Steps:
    - write temp file in same dir
    - flush + fsync temp file
    - os.replace(temp, target) (atomic rename)
    - fsync parent directory (durable rename/metadata)
    """
    target_path = Path(target)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_fd: Optional[int] = None
    tmp_path: Optional[Path] = None
    try:
        tmp_fd, tmp_name = tempfile.mkstemp(prefix=f".{target_path.name}.", dir=str(target_path.parent))
        tmp_path = Path(tmp_name)

        with os.fdopen(tmp_fd, "wb") as f:
            tmp_fd = None  # ownership transferred to file object
            f.write(data)
            f.flush()
            os.fsync(f.fileno())

        os.replace(str(tmp_path), str(target_path))
        _fsync_dir(target_path.parent)

    finally:
        # Cleanup temp file if anything failed before replace
        if tmp_fd is not None:
            try:
                os.close(tmp_fd)
            except Exception:
                pass
        if tmp_path is not None and tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass


def write_json_atomic(path: Path, obj: object) -> None:
    """Serialize obj as pretty JSON and write atomically + durably."""
    payload = json.dumps(
        obj,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    _atomic_write_bytes(Path(path), payload.encode("utf-8"))


def read_json(path: Path) -> object:
    """Read JSON data from path and return the deserialized object."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def append_jsonl(path: Path, obj: object) -> None:
    """Append one JSON object as a single JSONL line, durably."""
    line = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n"
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    with open(p, "ab") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())

    _fsync_dir(p.parent)


def write_text_atomic(path: Path, text: str) -> None:
    """Write text data atomically + durably using UTF-8."""
    _atomic_write_bytes(Path(path), text.encode("utf-8"))


def write_bytes_atomic(path: Path, data: bytes) -> None:
    """Write bytes atomically + durably."""
    _atomic_write_bytes(Path(path), data)

