"""RohTalk benchmark runner."""

from __future__ import annotations

import contextlib
import io
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from Core.LLMClient.client import LLMClient

from Core.RohTalk.config import resolve_model_profile
from Core.RohTalk.config import load_config
from Core.RohTalk.messages import assemble_initial_messages
from Core.RohTalk.orchestrator import _with_toolkit_guidance
from Core.RohTalk.skillcli_tools import execute_skill
from Core.RohTalk.tool_loop import run_tool_loop
from Core.RohTalk.toolkits import resolve_toolkit

from .cases import BenchmarkCase, get_cases, normalize_mode
from .results import BenchmarkResult, snippet


@dataclass(frozen=True)
class BenchmarkRequest:
    """Inputs for a RohTalk benchmark run."""

    suite: str = "smoke"
    mode: str = "no-tools"
    iterations: int = 1
    timeout_s: float = 180.0
    model: Optional[str] = None
    model_profile: Optional[str] = None
    host: Optional[str] = None
    model_options: Optional[Dict[str, Any]] = None
    toolkit: Optional[str] = None
    tools_enabled: Optional[bool] = None
    case_ids: Optional[List[str]] = None
    allow_live_dst_actions: bool = False


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _tool_names_from_messages(messages: List[Dict[str, Any]]) -> List[str]:
    names: List[str] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        tool_calls = message.get("tool_calls")
        if not isinstance(tool_calls, list):
            continue
        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                continue
            name = str(tool_call.get("name", "") or "").strip()
            if name:
                names.append(name)
    return names


def _arguments_by_tool(messages: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    result: Dict[str, List[Dict[str, Any]]] = {}
    for message in messages:
        if not isinstance(message, dict):
            continue
        tool_calls = message.get("tool_calls")
        if not isinstance(tool_calls, list):
            continue
        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                continue
            name = str(tool_call.get("name", "") or "").strip()
            arguments = tool_call.get("arguments") or {}
            if name and isinstance(arguments, dict):
                result.setdefault(name, []).append(dict(arguments))
    return result


def _expected_tools_present(expected: List[str], observed: List[str]) -> bool:
    if not expected:
        return True
    cursor = 0
    for name in observed:
        if cursor < len(expected) and name == expected[cursor]:
            cursor += 1
    return cursor == len(expected)


def _shape_value_matches(actual: Any, expected: Any) -> bool:
    if isinstance(expected, type):
        return isinstance(actual, expected)
    return actual == expected


def _expected_json_shape_met(case: BenchmarkCase, messages: List[Dict[str, Any]]) -> Optional[bool]:
    if not case.expected_arguments:
        return None

    by_tool = _arguments_by_tool(messages)
    for tool_name, expected_args in case.expected_arguments.items():
        calls = by_tool.get(tool_name, [])
        if not calls:
            return False

        matched = False
        for args in calls:
            if all(_shape_value_matches(args.get(key), expected) for key, expected in expected_args.items()):
                matched = True
                break
        if not matched:
            return False

    return True


def _dry_skill_executor(
    observed_results: List[Dict[str, Any]],
):
    def _execute(_ctx: Any, skill_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "dry_run": True,
            "skill_name": skill_name,
            "arguments": dict(arguments or {}),
        }
        observed_results.append(payload)
        return payload

    return _execute


def _live_skill_executor(allow_live_dst_actions: bool):
    if not allow_live_dst_actions:
        raise ValueError("dst-director-live requires --allow-live-dst-actions.")
    return execute_skill


def _resolve_toolkit_name(request: BenchmarkRequest, case: BenchmarkCase) -> Optional[str]:
    requested = str(request.toolkit or "").strip()
    if requested:
        return requested
    if request.mode in {"tool-dry", "dst-director-dry", "dst-director-live"}:
        return "dst_director"
    return case.toolkit


def _tools_enabled_for_case(request: BenchmarkRequest, case: BenchmarkCase) -> bool:
    if request.tools_enabled is not None:
        return bool(request.tools_enabled)
    if str(request.toolkit or "").strip():
        return True
    if request.mode in {"tool-dry", "dst-director-dry", "dst-director-live"}:
        return True
    return bool(case.default_tools)


def _result_mode(request: BenchmarkRequest, case: BenchmarkCase) -> str:
    return request.mode if request.mode == "tool-dry" else case.mode


def _run_no_tools_case(
    ctx: Any,
    case: BenchmarkCase,
    *,
    resolved_model: Any,
    timeout_s: float,
) -> Tuple[int, str, str, List[Dict[str, Any]], List[str]]:
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    messages: List[Dict[str, Any]] = []
    errors: List[str] = []

    with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
        config = load_config(ctx)
        client = LLMClient()
        result = client.chat(
            assemble_initial_messages(config.agent_identity, case.prompt),
            model=resolved_model.model,
            host=resolved_model.host,
            timeout_s=timeout_s,
            model_options=resolved_model.options,
        )
        reply = result.text
        stdout_buffer.write(reply)
        messages = [result.assistant_message]

    return 0, stdout_buffer.getvalue(), stderr_buffer.getvalue(), messages, errors


def _run_tool_case(
    ctx: Any,
    case: BenchmarkCase,
    *,
    request: BenchmarkRequest,
    resolved_model: Any,
    toolkit_name: str,
) -> Tuple[int, str, str, List[Dict[str, Any]], List[str]]:
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    errors: List[str] = []
    observed_results: List[Dict[str, Any]] = []

    toolkit = resolve_toolkit(toolkit_name)
    messages = assemble_initial_messages(
        "Use tools when they are relevant. After tool results, respond normally.",
        case.prompt,
    )
    messages = _with_toolkit_guidance(messages, toolkit.system_guidance)

    if request.mode in {"tool-dry", "dst-director-dry"}:
        skill_executor = _dry_skill_executor(observed_results)
    elif request.mode == "dst-director-live":
        skill_executor = _live_skill_executor(request.allow_live_dst_actions)
    else:
        if toolkit.name == "dst_director":
            skill_executor = _dry_skill_executor(observed_results)
        else:
            skill_executor = execute_skill

    with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
        final_text, final_messages = run_tool_loop(
            messages,
            model=resolved_model.model,
            host=resolved_model.host,
            model_options=resolved_model.options,
            timeout_s=request.timeout_s,
            tools=toolkit.tools,
            tool_impl=None,
            execution_mode="skillcli",
            ctx=ctx,
            skill_name_map=toolkit.skill_name_map,
            skill_executor=skill_executor,
            max_steps=5,
        )
        stdout_buffer.write(final_text)

    if observed_results:
        messages_out = list(final_messages)
        messages_out.append({"role": "benchmark", "observed_results": observed_results})
    else:
        messages_out = list(final_messages)

    return 0, stdout_buffer.getvalue(), stderr_buffer.getvalue(), messages_out, errors


def _run_case(
    ctx: Any,
    case: BenchmarkCase,
    *,
    request: BenchmarkRequest,
    resolved_model: Any,
) -> BenchmarkResult:
    start = time.monotonic()
    exit_code = 0
    stdout_text = ""
    stderr_text = ""
    messages: List[Dict[str, Any]] = []
    errors: List[str] = []
    tools_enabled = _tools_enabled_for_case(request, case)
    toolkit_name = _resolve_toolkit_name(request, case)

    try:
        if case.live and request.mode == "dst-director-live" and not request.allow_live_dst_actions:
            raise ValueError("dst-director-live requires --allow-live-dst-actions.")

        if tools_enabled:
            if not toolkit_name:
                toolkit_name = "basic"
            exit_code, stdout_text, stderr_text, messages, errors = _run_tool_case(
                ctx,
                case,
                request=request,
                resolved_model=resolved_model,
                toolkit_name=toolkit_name,
            )
        else:
            exit_code, stdout_text, stderr_text, messages, errors = _run_no_tools_case(
                ctx,
                case,
                resolved_model=resolved_model,
                timeout_s=request.timeout_s,
            )
    except Exception as exc:
        exit_code = 1
        errors.append(str(exc))
        stderr_text = str(exc)

    elapsed = time.monotonic() - start
    observed_tool_names = _tool_names_from_messages(messages)
    expected_shape = _expected_json_shape_met(case, messages)
    tool_match = _expected_tools_present(case.expected_tool_names, observed_tool_names)

    success = (
        exit_code == 0
        and (bool(str(stdout_text).strip()) or bool(observed_tool_names))
        and tool_match
        and expected_shape is not False
    )
    if not tool_match:
        errors.append(
            "Expected tool sequence not observed: "
            + ",".join(case.expected_tool_names)
        )
    if expected_shape is False:
        errors.append("Expected tool argument shape was not observed.")

    return BenchmarkResult(
        timestamp=_iso_now(),
        case_id=case.case_id,
        mode=_result_mode(request, case),
        suite=request.suite,
        model=str(resolved_model.model),
        model_profile=resolved_model.profile_name,
        toolkit=toolkit_name if tools_enabled else None,
        tools_enabled=tools_enabled,
        host=resolved_model.host,
        model_options=dict(resolved_model.options or {}),
        elapsed_seconds=round(elapsed, 4),
        exit_code=exit_code,
        success=success,
        expected_tool_names=list(case.expected_tool_names),
        observed_tool_names=observed_tool_names,
        expected_json_shape_met=expected_shape,
        stdout_snippet=snippet(stdout_text),
        stderr_snippet=snippet(stderr_text),
        notes=case.notes,
        errors=errors,
    )


def run_benchmark(ctx: Any, request: BenchmarkRequest) -> List[BenchmarkResult]:
    """Run benchmark cases and return result rows."""
    iterations = max(1, int(request.iterations or 1))
    mode = normalize_mode(request.mode)
    normalized_request = BenchmarkRequest(
        suite=request.suite,
        mode=mode,
        iterations=request.iterations,
        timeout_s=request.timeout_s,
        model=request.model,
        model_profile=request.model_profile,
        host=request.host,
        model_options=request.model_options,
        toolkit=request.toolkit,
        tools_enabled=request.tools_enabled,
        case_ids=request.case_ids,
        allow_live_dst_actions=request.allow_live_dst_actions,
    )
    cases = get_cases(suite=request.suite, mode=mode, case_ids=request.case_ids)
    resolved_model = resolve_model_profile(
        ctx,
        normalized_request.model_profile,
        model_override=normalized_request.model,
        host_override=normalized_request.host,
        option_overrides=normalized_request.model_options,
    )

    results: List[BenchmarkResult] = []
    for _iteration in range(iterations):
        for case in cases:
            results.append(
                _run_case(
                    ctx,
                    case,
                    request=normalized_request,
                    resolved_model=resolved_model,
                )
            )
    return results
