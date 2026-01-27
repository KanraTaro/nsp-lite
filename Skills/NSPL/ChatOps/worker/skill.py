from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from Core.NSPL.ChatOps import claim as _claim
from Core.NSPL.ChatOps import store as _store
from Core.NSPL.ChatOps import task_schema as _task_schema
from Core.NSPL.ChatOps import transitions as _transitions
from Core.NSPL.NodeCTX import JsonlRotationPolicy, JsonlThrottlePolicy

def _now_utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--domain",
        default="ChatOps",
        help="ChatOps domain used to locate queue directories (default: ChatOps)",
    )
    parser.add_argument(
        "--worker-id",
        dest="worker_id",
        default=None,
        help="Optional identifier for this worker; defaults to the node tag",
    )
    parser.add_argument(
        "--poll-ms",
        dest="poll_ms",
        type=float,
        default=1000.0,
        help="Polling interval in milliseconds when no tasks are available",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process at most one task then exit",
    )

    # Logging controls (disk safety knobs)
    parser.add_argument(
        "--idle-heartbeat-sec",
        dest="idle_heartbeat_sec",
        type=float,
        default=0.0,
        help="If >0, write an idle heartbeat event at most once every N seconds while idle (default: 0 = off)",
    )
    parser.add_argument(
        "--log-max-bytes",
        dest="log_max_bytes",
        type=int,
        default=256_000,
        help="Rotate events jsonl when it exceeds this size in bytes (default: 256000). Use 0 to disable rotation.",
    )
    parser.add_argument(
        "--log-keep",
        dest="log_keep",
        type=int,
        default=5,
        help="Number of rotated jsonl files to keep (default: 5)",
    )
    parser.add_argument(
        "--quiet-idle",
        dest="quiet_idle",
        action="store_true",
        help="Do not print '[chatops.worker] idle' repeatedly (still logs state changes).",
    )


def run(args: argparse.Namespace, ctx: Any) -> int:
    root: Path = ctx.root
    instance_id: str = ctx.instance_id
    node_ctx = ctx.node_ctx
    node_tag: str = ctx.node_tag

    domain: str = str(args.domain)
    poll_sec: float = float(args.poll_ms) / 1000.0 if args.poll_ms is not None else 1.0

    worker_id: str = str(args.worker_id) if args.worker_id else str(node_tag)

    inbox_dir, claimed_dir, done_dir, failed_dir = _store.get_queue_dirs(
        node_ctx, root, instance_id, domain=domain
    )

    chatops_base: Path = inbox_dir.parent

    # Events log location (global scope for ChatOps system visibility)
    logs_dir: Path = node_ctx.build_state_dir(
        root=root,
        instance_id=instance_id,
        node_tag=node_tag,
        bucket="Logs",
        domain=domain,
        global_scope=True,
        subpath="worker",
    )
    events_path: Path = logs_dir / f"{worker_id}.events.jsonl"

    idle_heartbeat_sec: float = float(getattr(args, "idle_heartbeat_sec", 0.0) or 0.0)
    log_max_bytes: int = int(getattr(args, "log_max_bytes", 256_000) or 0)
    log_keep: int = int(getattr(args, "log_keep", 5) or 5)
    quiet_idle: bool = bool(getattr(args, "quiet_idle", False))
    printed_idle_once: bool = False
    print(f"[chatops.worker] start: worker_id={worker_id} instance={instance_id} node={node_tag} domain={domain}", flush=True)

    last_state: str = "init"

    rotation_policy: JsonlRotationPolicy = JsonlRotationPolicy(
        max_bytes=log_max_bytes,
        keep=log_keep,
    )

    idle_throttle_policy: Optional[JsonlThrottlePolicy] = None
    if idle_heartbeat_sec > 0.0:
        idle_throttle_policy = JsonlThrottlePolicy(min_interval_sec=idle_heartbeat_sec)

    def build_base() -> Dict[str, Any]:
        return {
            "ts_utc": _now_utc_iso(),
            "worker_id": worker_id,
            "instance": instance_id,
            "node": str(node_tag),
            "domain": domain,
            "pid": int(os.getpid()),
        }

    def log_event(
        kind: str,
        extra: Optional[Dict[str, Any]] = None,
        *,
        rotation: Optional[JsonlRotationPolicy] = None,
        throttle: Optional[JsonlThrottlePolicy] = None,
        throttle_key: Optional[str] = None,
    ) -> None:
        node_ctx.log_event_jsonl(
            path=events_path,
            kind=kind,
            base=build_base(),
            extra=extra,
            rotation=rotation if rotation is not None else rotation_policy,
            throttle=throttle,
            throttle_key=throttle_key,
        )

    def set_state(new_state: str) -> None:
        nonlocal last_state
        if new_state == last_state:
            return
        last_state = new_state
        log_event("state", {"state": new_state})
        
    def _guess_task_id_from_filename(name: str) -> str:
        stem = Path(name).stem
        parts = stem.split("__")
        if len(parts) >= 3:
            return parts[-1]
        return stem

    def process_one(task_path: Path) -> bool:
        claimed: Optional[Path] = _claim.claim_task(task_path, claimed_dir)
        if claimed is None:
            return False
            
        nonlocal printed_idle_once
        printed_idle_once = False

        set_state("claimed")
        print(f"[chatops.worker] claimed: {claimed.name}", flush=True)
        log_event("claimed", {"file": claimed.name})

        try:
            payload_obj = node_ctx.read_json(claimed)
        except Exception as ex:
            result = {
                "task_id": claimed.stem,
                "task_id": _guess_task_id_from_filename(claimed.name),
                "finished_utc": _now_utc_iso(),
                "status": "failed",
                "exit_code": -1,
                "worker_id": worker_id,
                "skill": "<unknown>",
                "args": [],
                "error": {"type": ex.__class__.__name__, "message": str(ex)},
            }
            _transitions.fail_task(node_ctx, claimed, failed_dir, result)
            log_event("failed_unreadable_json", {"file": claimed.name, "error": str(ex)})
            return True

        try:
            _task_schema.validate_task(payload_obj)
        except Exception as ex:
            result = {
                "task_id": payload_obj.get("task_id", claimed.stem),
                "finished_utc": _now_utc_iso(),
                "status": "failed",
                "exit_code": -1,
                "worker_id": worker_id,
                "skill": payload_obj.get("skill", "<unknown>"),
                "args": payload_obj.get("args", []),
                "error": {"type": ex.__class__.__name__, "message": str(ex)},
            }
            _transitions.fail_task(node_ctx, claimed, failed_dir, result)
            log_event("failed_schema", {"file": claimed.name, "error": str(ex)})
            return True

        payload: Dict[str, Any] = dict(payload_obj)

        ctx_info: Dict[str, Any] = payload.get("ctx", {}) if isinstance(payload.get("ctx"), dict) else {}
        target_node = ctx_info.get("node_id")

        # Routing decision: tasks can be targeted; worker should only execute if it matches.
        if target_node and target_node not in (node_tag, "Any", "any"):
            try:
                os.replace(str(claimed), str(inbox_dir / claimed.name))
            except Exception:
                pass
            log_event(
                "returned_to_inbox_wrong_target",
                {"file": claimed.name, "target_node": str(target_node)},
            )
            return False

        skill_name: str = str(payload.get("skill"))
        skill_args: List[str] = list(payload.get("args", [])) if isinstance(payload.get("args"), list) else []

        set_state("exec")
        print(f"[chatops.worker] exec: {skill_name} ({len(skill_args)} args)", flush=True)
        log_event("exec_start", {"file": claimed.name, "skill": skill_name, "args_count": len(skill_args)})

        cli_cmd: List[str] = [sys.executable, "-m", "Core.NSPL.SkillCLI", "skill", skill_name]
        cli_cmd.extend(["--instance", instance_id])

        # IMPORTANT: worker executes as itself, not as the target label.
        cli_cmd.extend(["--node", str(node_tag)])

        cli_cmd.extend(skill_args)

        start_t = time.monotonic()
        try:
            proc = subprocess.run(cli_cmd, capture_output=True, text=True)
            exit_code = int(proc.returncode)
            stdout = proc.stdout
            stderr = proc.stderr
        except Exception as ex:
            exit_code = -1
            stdout = ""
            stderr = f"{ex.__class__.__name__}: {ex}"

        duration_ms = int((time.monotonic() - start_t) * 1000)
        status = "done" if exit_code == 0 else "failed"

        result: Dict[str, Any] = {
            "task_id": payload.get("task_id"),
            "finished_utc": _now_utc_iso(),
            "status": status,
            "exit_code": exit_code,
            "duration_ms": duration_ms,
            "worker_id": worker_id,
            "skill": skill_name,
            "args": skill_args,
            "stdout": stdout,
            "stderr": stderr,
        }

        if status == "done":
            _transitions.complete_task(node_ctx, claimed, done_dir, result)
        else:
            _transitions.fail_task(node_ctx, claimed, failed_dir, result)

        log_event(
            "exec_done",
            {
                "file": claimed.name,
                "status": status,
                "exit_code": exit_code,
                "duration_ms": duration_ms,
            },
        )
        print(f"[chatops.worker] {status}: exit={exit_code} ms={duration_ms} file={claimed.name}", flush=True)

        reply = payload.get("reply_to")
        if isinstance(reply, dict) and reply.get("mode") == "file":
            path = reply.get("path")
            if isinstance(path, str) and path:
                out_path = chatops_base / path
                try:
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    node_ctx.write_json_atomic(out_path, result)
                    log_event("reply_to_written", {"path": str(path)})
                except Exception as ex:
                    log_event("reply_to_failed", {"path": str(path), "error": str(ex)})

        return True

    processed_any = False
    set_state("idle")

    while True:
        tasks = _store.list_tasks(inbox_dir)
        if not tasks:
            # Only print once when entering idle, unless quiet_idle is false and you want it spammy.
            if not quiet_idle and not printed_idle_once:
                print("[chatops.worker] idle", flush=True)
                printed_idle_once = True

            set_state("idle")

            if idle_throttle_policy is not None:
                log_event(
                    "idle_heartbeat",
                    throttle=idle_throttle_policy,
                    throttle_key="idle_heartbeat",
                )

            if args.once and processed_any:
                break

            time.sleep(poll_sec)
            continue

        for task_path in tasks:
            handled = process_one(task_path)
            if handled:
                processed_any = True
                if args.once:
                    set_state("idle")
                    return 0

        if args.once and processed_any:
            break

        time.sleep(poll_sec)

    set_state("idle")
    return 0

