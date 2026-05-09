"""Reusable AutoRoh loop execution."""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from Core.AutoRoh.notes import get_messages, latest_unhandled_note
from Core.AutoRoh.observations import call_observation_tool
from Core.AutoRoh.prompts import DEFAULT_LOOP_PROMPT, build_tick_prompt
from Core.AutoRoh.profiles import AutoRohProfile, resolve_autoroh_profile
from Core.AutoRoh.state import (
    load_loop_state,
    mark_idle_skip,
    reset_idle_skip,
    save_loop_state,
    update_after_tick,
    update_observation,
)
from Core.AutoRoh.tool_events import (
    action_signature_from_tool_events,
    record_tool_call,
    record_tool_result,
)
from Core.LLMClient.types import LLMClientError
from Core.RohTalk import run_turn
from Core.RohTalk.tracing import print_step, print_tool_call, print_tool_result


def _build_action_tool_stop_callback(
    profile: AutoRohProfile,
    *,
    has_new_note: bool,
) -> Optional[Callable[[Dict[str, Any]], bool]]:
    max_action_tools = profile.action_tool_budget_for_tick(has_human_note=has_new_note)
    if not profile.action_tool_names or max_action_tools is None:
        return None

    action_tool_names = set(profile.action_tool_names)
    successful_action_tools = 0

    def should_stop_after_tool_result(tool_result: Dict[str, Any]) -> bool:
        nonlocal successful_action_tools

        if not bool(tool_result.get("ok", False)):
            return False

        tool_name = str(tool_result.get("tool_name", "") or "")
        if tool_name not in action_tool_names:
            return False

        successful_action_tools += 1
        return successful_action_tools >= max_action_tools

    return should_stop_after_tool_result


@dataclass(frozen=True)
class AutoRohLoopConfig:
    conversation_id: Optional[str] = None
    prompt: str = DEFAULT_LOOP_PROMPT
    interval: float = 10.0
    max_turns: int = 5
    forever: bool = False
    title: str = "AutoRoh Loop"
    model: Optional[str] = None
    host: Optional[str] = None
    tools: bool = False
    tool_backend: str = "skillcli"
    toolkit: str = "basic"
    tool_trace: bool = False
    idle_skip: bool = False
    observation_tool: Optional[str] = None


def run_autoroh_loop(ctx: Any, config: AutoRohLoopConfig) -> int:
    """Run the AutoRoh loop with an already resolved conversation id."""
    conversation_id = config.conversation_id
    max_turns = int(config.max_turns)
    interval = float(config.interval)
    forever = bool(config.forever)
    tool_trace = bool(config.tool_trace)
    profile = resolve_autoroh_profile(str(config.toolkit) if config.tools else "basic")

    if not forever and max_turns <= 0:
        print("max-turns must be greater than 0 unless --forever is used.", file=sys.stderr)
        return 2

    if interval < 0:
        print("interval must be 0 or greater.", file=sys.stderr)
        return 2

    prompt = str(config.prompt or DEFAULT_LOOP_PROMPT).strip()
    if prompt == "":
        print("prompt cannot be empty.", file=sys.stderr)
        return 2

    observation_tool = config.observation_tool
    observation_tool = str(observation_tool).strip() if observation_tool else None

    print("AutoRoh loop starting.")
    print(f"conversation: {conversation_id or '(new)'}")
    print(f"max_turns: {'forever' if forever else max_turns}")
    print(f"interval: {interval}")
    print(f"tools: {bool(config.tools)}")
    if config.tools:
        print(f"tool_backend: {config.tool_backend}")
        print(f"toolkit: {config.toolkit}")
        print(f"tool_trace: {tool_trace}")
        print(f"idle_skip: {bool(config.idle_skip)}")
        if observation_tool:
            print(f"observation_tool: {observation_tool}")
    print("")

    try:
        turn_index = 0

        while forever or turn_index < max_turns:
            turn_index += 1
            total_label = "∞" if forever else str(max_turns)
            print(f"[AutoRoh turn {turn_index}/{total_label}]")

            latest_note_index: Optional[int] = None
            has_new_note = False
            tick_prompt = prompt
            observation_signature: Optional[str] = None
            observation_summary: Optional[str] = None
            observation_changed = True

            if conversation_id is not None:
                state = load_loop_state(ctx, conversation_id)

                if observation_tool:
                    observation_signature, observation_summary = call_observation_tool(
                        ctx,
                        toolkit_name=str(config.toolkit),
                        tool_name=observation_tool,
                    )
                    previous_signature = state.get("last_observation_signature")
                    observation_changed = observation_signature != previous_signature

                latest_note_index, latest_note = latest_unhandled_note(
                    ctx,
                    conversation_id,
                    int(state.get("last_human_note_index", -1)),
                )

                has_new_note = latest_note_index is not None

                if config.idle_skip and observation_tool and not observation_changed and not has_new_note:
                    mark_idle_skip(state)
                    update_observation(
                        state,
                        observation_signature=observation_signature,
                        observation_summary=observation_summary,
                    )
                    save_loop_state(ctx, state)
                    print(f"conversation_id: {conversation_id}")
                    print("(idle skip: no new note or observation change)")

                    should_continue = forever or turn_index < max_turns
                    if should_continue and interval > 0:
                        time.sleep(interval)
                    continue

                reset_idle_skip(state)
                update_observation(
                    state,
                    observation_signature=observation_signature,
                    observation_summary=observation_summary,
                )
                save_loop_state(ctx, state)

                tick_prompt = build_tick_prompt(prompt, state, latest_note, profile=profile)

                if observation_summary:
                    tick_prompt += "\nObservation:\n"
                    tick_prompt += observation_summary
                    tick_prompt += "\n"

            tool_events: List[Dict[str, Any]] = []

            def on_step(step_index: int) -> None:
                if tool_trace:
                    print_step(step_index)

            def on_tool_call(tool_call: Any) -> None:
                tool_events.append(record_tool_call(tool_call))
                if tool_trace:
                    print_tool_call(tool_call)

            def on_tool_result(tool_result: Dict[str, Any]) -> None:
                tool_events.append(record_tool_result(tool_result))
                if tool_trace:
                    print_tool_result(tool_result)

            should_stop_after_tool_result = None
            if config.tools:
                should_stop_after_tool_result = _build_action_tool_stop_callback(
                    profile,
                    has_new_note=has_new_note,
                )

            conversation_id, reply = run_turn(
                ctx,
                tick_prompt,
                conversation_id=conversation_id,
                kind="conversation",
                model=config.model,
                host=config.host,
                title=config.title,
                use_tools=bool(config.tools),
                tool_backend=str(config.tool_backend),
                toolkit=str(config.toolkit),
                on_step=on_step if config.tools and tool_trace else None,
                on_tool_call=on_tool_call if config.tools else None,
                on_tool_result=on_tool_result if config.tools else None,
                should_stop_after_tool_result=should_stop_after_tool_result,
            )

            print(f"conversation_id: {conversation_id}")

            if reply:
                print(reply)
            else:
                print("(empty reply)")

            state = load_loop_state(ctx, conversation_id)
            message_count = len(get_messages(ctx, conversation_id))
            action_signature: Optional[str] = action_signature_from_tool_events(
                tool_events,
                action_tool_names=profile.action_tool_names,
            )

            if action_signature is None and reply and str(reply).strip() != "wait":
                action_signature = str(reply).strip()[:160]

            update_after_tick(
                ctx,
                state,
                message_count=message_count,
                last_note_index=latest_note_index,
                action_signature=action_signature,
            )
            save_loop_state(ctx, state)

            should_continue = forever or turn_index < max_turns
            if should_continue and interval > 0:
                time.sleep(interval)

        print("")
        print("AutoRoh loop finished.")
        return 0

    except KeyboardInterrupt:
        print("")
        print("AutoRoh loop interrupted.")
        if conversation_id:
            print(f"conversation_id: {conversation_id}")
        return 130
    except LLMClientError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
