"""Result formatting and persistence for RohTalk benchmarks."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class BenchmarkResult:
    """Serializable benchmark result row."""

    timestamp: str
    case_id: str
    mode: str
    suite: str
    model: str
    model_profile: Optional[str]
    toolkit: Optional[str]
    tools_enabled: bool
    host: Optional[str]
    model_options: Dict[str, Any]
    elapsed_seconds: float
    exit_code: int
    success: bool
    expected_tool_names: List[str]
    observed_tool_names: List[str]
    expected_json_shape_met: Optional[bool]
    stdout_snippet: str
    stderr_snippet: str
    notes: str
    errors: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def snippet(value: Any, *, limit: int = 500) -> str:
    text = str(value or "")
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def format_summary(results: List[BenchmarkResult]) -> str:
    """Return a compact human-readable benchmark summary."""
    if not results:
        return "No benchmark results."

    headers = ["case", "mode", "success", "elapsed", "tools", "error"]
    rows: List[List[str]] = []
    for result in results:
        rows.append(
            [
                result.case_id,
                result.mode,
                "yes" if result.success else "no",
                f"{result.elapsed_seconds:.2f}s",
                ",".join(result.observed_tool_names) or "-",
                "; ".join(result.errors)[:80] if result.errors else "-",
            ]
        )

    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]
    lines = [
        "  ".join(headers[index].ljust(widths[index]) for index in range(len(headers))),
        "  ".join("-" * width for width in widths),
    ]
    for row in rows:
        lines.append("  ".join(row[index].ljust(widths[index]) for index in range(len(headers))))

    success_count = sum(1 for result in results if result.success)
    lines.append("")
    lines.append(f"Summary: {success_count}/{len(results)} cases passed.")
    return "\n".join(lines)


def save_results_jsonl(ctx: Any, results: List[BenchmarkResult]) -> Path:
    """Append benchmark results to RohTalk Logs/Benchmarks JSONL."""
    node_ctx = ctx.node_ctx
    out_dir = node_ctx.build_state_dir(
        root=ctx.root,
        instance_id=ctx.instance_id,
        node_tag=ctx.node_tag,
        bucket="Logs",
        domain="RohTalk",
        global_scope=ctx.global_scope,
        subpath="Benchmarks",
    )
    node_ctx.ensure_dir(out_dir)
    out_path = out_dir / "rohtalk_benchmark.jsonl"

    for result in results:
        node_ctx.append_jsonl(out_path, result.to_dict())

    return out_path


def save_results_markdown(ctx: Any, results: List[BenchmarkResult]) -> Path:
    """Write a markdown benchmark summary to RohTalk Logs/Benchmarks."""
    node_ctx = ctx.node_ctx
    out_dir = node_ctx.build_state_dir(
        root=ctx.root,
        instance_id=ctx.instance_id,
        node_tag=ctx.node_tag,
        bucket="Logs",
        domain="RohTalk",
        global_scope=ctx.global_scope,
        subpath="Benchmarks",
    )
    node_ctx.ensure_dir(out_dir)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"rohtalk_benchmark_{timestamp}.md"

    lines = [
        "# RohTalk Benchmark",
        "",
        format_summary(results),
        "",
        "## Results",
        "",
        "| case | mode | model | profile | toolkit | tools | success | elapsed | observed tools | errors |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for result in results:
        lines.append(
            "| "
            + " | ".join(
                [
                    result.case_id,
                    result.mode,
                    result.model,
                    result.model_profile or "",
                    result.toolkit or "",
                    "yes" if result.tools_enabled else "no",
                    "yes" if result.success else "no",
                    f"{result.elapsed_seconds:.2f}s",
                    ",".join(result.observed_tool_names),
                    "; ".join(result.errors),
                ]
            )
            + " |"
        )
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


def save_results(ctx: Any, results: List[BenchmarkResult]) -> Dict[str, Path]:
    """Save JSONL and markdown benchmark outputs."""
    return {
        "jsonl": save_results_jsonl(ctx, results),
        "markdown": save_results_markdown(ctx, results),
    }


def results_to_json(
    results: List[BenchmarkResult],
    *,
    saved_path: Optional[Path] = None,
    saved_paths: Optional[Dict[str, Path]] = None,
) -> str:
    payload: Dict[str, Any] = {
        "results": [result.to_dict() for result in results],
    }
    if saved_path is not None:
        payload["saved_path"] = str(saved_path)
    if saved_paths is not None:
        payload["saved_paths"] = {key: str(value) for key, value in saved_paths.items()}
    return json.dumps(payload, indent=2, sort_keys=True)
