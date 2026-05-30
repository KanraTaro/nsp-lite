from __future__ import annotations

import fnmatch
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DEFAULT_EXCLUDES: tuple[str, ...] = (
    "State/**",
    ".git/**",
    "**/__pycache__/**",
    ".pytest_cache/**",
    "*.egg-info/**",
    "**/*.egg-info/**",
    "**/*.pyc",
    ".venv/**",
    "venv/**",
    "node_modules/**",
    ".obsidian/**",
    ".trash/**",
    ".stfolder/**",
    "Bundles/**",
    "Docs/Bundles/*.md",
    "Docs/Bundles/generated/**",
    "Docs/nsp-project-log-*.txt",
    "nsp-project-log-*.txt",
    "Logs/**",
    "logs/**",
    "Archive/**",
    "Archives/**",
    "Backups/**",
)


class BundleError(ValueError):
    """Raised when a documentation bundle cannot be produced safely."""


@dataclass(frozen=True)
class BundleResult:
    bundle: str
    mode: str
    target: str
    output: str
    sources: list[str]
    manifest: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_target_folder(target: str | Path | None = None) -> Path:
    if target:
        return Path(target).expanduser().resolve()
    caller_cwd = os.environ.get("NSPL_CALLER_CWD")
    if caller_cwd:
        return Path(caller_cwd).expanduser().resolve()
    return Path.cwd().resolve()


def find_manifest(target: Path) -> Path | None:
    docs_manifest = target / "Docs" / "Bundles" / "bundles.json"
    generic_manifest = target / "Bundles" / "bundles.json"
    if docs_manifest.is_file():
        return docs_manifest
    if generic_manifest.is_file():
        return generic_manifest
    return None


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BundleError(f"invalid bundle manifest JSON: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise BundleError(f"bundle manifest must be a JSON object: {path}")
    bundles = data.get("bundles")
    if not isinstance(bundles, dict) or not bundles:
        raise BundleError(f"bundle manifest has no bundles: {path}")
    return data


def list_bundles(target: str | Path | None = None) -> dict[str, Any]:
    target_path = resolve_target_folder(target)
    manifest_path = find_manifest(target_path)
    if manifest_path is None:
        return {
            "target": str(target_path),
            "manifest": None,
            "auto_available": True,
            "bundles": [],
            "default": None,
        }
    manifest = _load_manifest(manifest_path)
    bundles = manifest["bundles"]
    default_name = _default_bundle_name(manifest)
    return {
        "target": str(target_path),
        "manifest": str(manifest_path),
        "auto_available": True,
        "default": default_name,
        "bundles": [
            {
                "name": name,
                "description": _bundle_config(config).get("description", ""),
                "default": name == default_name,
            }
            for name, config in sorted(bundles.items())
        ],
    }


def generate_default(
    target: str | Path | None = None,
    *,
    output_name: str | None = None,
) -> BundleResult:
    target_path = resolve_target_folder(target)
    manifest_path = find_manifest(target_path)
    if manifest_path is None:
        return generate_auto_bundle(target_path, output_name=output_name)
    manifest = _load_manifest(manifest_path)
    return _generate_manifest_bundle(target_path, manifest_path, manifest, _default_bundle_name(manifest), output_name=output_name)


def generate_all(target: str | Path | None = None) -> list[BundleResult]:
    target_path = resolve_target_folder(target)
    manifest_path = find_manifest(target_path)
    if manifest_path is None:
        return [generate_auto_bundle(target_path)]
    manifest = _load_manifest(manifest_path)
    return [
        _generate_manifest_bundle(target_path, manifest_path, manifest, name)
        for name in sorted(manifest["bundles"].keys())
    ]


def generate_bundle(
    name: str,
    target: str | Path | None = None,
    *,
    output_name: str | None = None,
) -> BundleResult:
    target_path = resolve_target_folder(target)
    manifest_path = find_manifest(target_path)
    if manifest_path is None:
        raise BundleError(f"no bundle manifest found under target: {target_path}")
    manifest = _load_manifest(manifest_path)
    return _generate_manifest_bundle(target_path, manifest_path, manifest, name, output_name=output_name)


def generate_auto_bundle(
    target: str | Path | None = None,
    *,
    output_name: str | None = None,
) -> BundleResult:
    target_path = resolve_target_folder(target)
    sources = _discover_markdown(target_path, DEFAULT_EXCLUDES)
    output = _safe_output_path(target_path, output_name or "PROJECT_CONTEXT.md", default_dir="Bundles")
    _write_bundle(
        target=target_path,
        output=output,
        bundle_name="auto",
        sources=sources,
    )
    return BundleResult(
        bundle="auto",
        mode="auto",
        target=str(target_path),
        output=str(output),
        sources=[_rel(target_path, source) for source in sources],
        manifest=None,
    )


def _default_bundle_name(manifest: dict[str, Any]) -> str:
    explicit = manifest.get("default")
    bundles = manifest["bundles"]
    if isinstance(explicit, str) and explicit in bundles:
        return explicit
    for name, config in bundles.items():
        if isinstance(config, dict) and config.get("default") is True:
            return name
    return sorted(bundles.keys())[0]


def _bundle_config(config: Any) -> dict[str, Any]:
    if not isinstance(config, dict):
        raise BundleError("bundle config must be an object")
    return config


def _generate_manifest_bundle(
    target: Path,
    manifest_path: Path,
    manifest: dict[str, Any],
    name: str,
    *,
    output_name: str | None = None,
) -> BundleResult:
    bundles = manifest["bundles"]
    if name not in bundles:
        raise BundleError(f"bundle not found in manifest: {name}")
    config = _bundle_config(bundles[name])
    sources = _expand_sources(target, config, _combined_excludes(manifest, config))
    output = _manifest_output_path(target, manifest, config, name, output_name=output_name)
    _write_bundle(target=target, output=output, bundle_name=name, sources=sources)
    return BundleResult(
        bundle=name,
        mode="manifest",
        target=str(target),
        output=str(output),
        sources=[_rel(target, source) for source in sources],
        manifest=str(manifest_path),
    )


def _combined_excludes(manifest: dict[str, Any], config: dict[str, Any]) -> list[str]:
    excludes = list(DEFAULT_EXCLUDES)
    for source in (manifest.get("exclude_globs"), config.get("exclude_globs")):
        if isinstance(source, list):
            excludes.extend(str(item) for item in source if isinstance(item, str))
    return excludes


def _expand_sources(target: Path, config: dict[str, Any], excludes: list[str]) -> list[Path]:
    raw_sources = config.get("sources")
    if not isinstance(raw_sources, list) or not raw_sources:
        raise BundleError("bundle config must include a non-empty sources list")

    expanded: list[Path] = []
    seen: set[Path] = set()
    for entry in raw_sources:
        paths = _expand_source_entry(target, entry, excludes)
        for path in paths:
            if path not in seen:
                seen.add(path)
                expanded.append(path)
    return expanded


def _expand_source_entry(target: Path, entry: Any, excludes: list[str]) -> list[Path]:
    optional = False
    if isinstance(entry, str):
        pattern = entry
    elif isinstance(entry, dict):
        raw_pattern = entry.get("path") or entry.get("glob")
        if not isinstance(raw_pattern, str):
            raise BundleError(f"invalid source entry: {entry!r}")
        pattern = raw_pattern
        optional = bool(entry.get("optional", False))
    else:
        raise BundleError(f"invalid source entry: {entry!r}")

    if Path(pattern).is_absolute():
        raise BundleError(f"source paths must be relative to target: {pattern}")

    has_glob = any(char in pattern for char in "*?[")
    if has_glob:
        matches = sorted(
            (path for path in target.glob(pattern) if path.is_file() and not _is_excluded(target, path, excludes)),
            key=lambda path: _rel(target, path),
        )
        if not matches and not optional:
            raise BundleError(f"source glob matched no files: {pattern}")
        return matches

    path = (target / pattern).resolve()
    _require_inside(target, path, "source")
    if not path.is_file():
        if optional:
            return []
        raise BundleError(f"missing source file: {pattern}")
    if _is_excluded(target, path, excludes):
        if optional:
            return []
        raise BundleError(f"source file is excluded: {pattern}")
    return [path]


def _discover_markdown(target: Path, excludes: Iterable[str]) -> list[Path]:
    return sorted(
        (path for path in target.rglob("*.md") if path.is_file() and not _is_excluded(target, path, excludes)),
        key=lambda path: _rel(target, path),
    )


def _is_excluded(target: Path, path: Path, excludes: Iterable[str]) -> bool:
    rel = _rel(target, path)
    parts = set(Path(rel).parts)
    if any(part in {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules"} for part in parts):
        return True
    for pattern in excludes:
        normalized = pattern.replace("\\", "/")
        if fnmatch.fnmatch(rel, normalized) or fnmatch.fnmatch("/" + rel, "/" + normalized):
            return True
        if normalized.endswith("/**") and rel.startswith(normalized[:-3].rstrip("/") + "/"):
            return True
    return False


def _manifest_output_path(
    target: Path,
    manifest: dict[str, Any],
    config: dict[str, Any],
    name: str,
    *,
    output_name: str | None,
) -> Path:
    if output_name:
        return _safe_output_path(target, output_name, default_dir="Bundles")
    output = config.get("output")
    if isinstance(output, str) and output.strip():
        return _safe_output_path(target, output, default_dir="Bundles")
    output_dir = manifest.get("output_dir")
    if isinstance(output_dir, str) and output_dir.strip():
        return _safe_output_path(target, str(Path(output_dir) / f"{name}.md"), default_dir="Bundles")
    return _safe_output_path(target, f"{name}.md", default_dir="Bundles")


def _safe_output_path(target: Path, output: str, *, default_dir: str) -> Path:
    raw = Path(output)
    path = raw if raw.is_absolute() else target / (raw if raw.parent != Path(".") else Path(default_dir) / raw.name)
    path = path.expanduser().resolve()
    _require_inside(target, path, "output")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _require_inside(target: Path, path: Path, label: str) -> None:
    try:
        path.relative_to(target.resolve())
    except ValueError as exc:
        raise BundleError(f"{label} path must stay inside target folder: {path}") from exc


def _write_bundle(*, target: Path, output: Path, bundle_name: str, sources: list[Path]) -> None:
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    lines: list[str] = [
        f"# Documentation Bundle: {bundle_name}",
        "",
        f"Generated: {timestamp}",
        f"Target folder: {target}",
        f"Bundle name: {bundle_name}",
        "",
        "Generated bundles are artifacts. Do not edit this file directly; edit source docs and regenerate it.",
        "",
        "## Source Files",
        "",
    ]
    if sources:
        lines.extend(f"- {_rel(target, source)}" for source in sources)
    else:
        lines.append("- No source files found.")
    lines.append("")

    for source in sources:
        rel = _rel(target, source)
        text = source.read_text(encoding="utf-8", errors="replace")
        lines.extend(
            [
                "---",
                "",
                f"# Source: {rel}",
                "",
                text.rstrip(),
                "",
            ]
        )

    output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _rel(target: Path, path: Path) -> str:
    return path.resolve().relative_to(target.resolve()).as_posix()
