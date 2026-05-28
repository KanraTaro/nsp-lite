from __future__ import annotations

from pathlib import Path
from typing import Any

import Core.NSPL.NodeCTX as node_ctx

DOMAIN = "LifeRPG"


class LifeRPGStore:
    def __init__(
        self,
        root: Path,
        *,
        instance_id: str = "main",
        node_tag: str | None = None,
        global_scope: bool = True,
    ) -> None:
        self.root = Path(root)
        self.instance_id = instance_id
        self.node_tag = node_tag or node_ctx.get_default_node_tag()
        self.global_scope = bool(global_scope)
        self.node_ctx = node_ctx

    def dir(self, bucket: str, subpath: str | list[str] | tuple[str, ...] | None = None) -> Path:
        return self.node_ctx.build_state_dir(
            root=self.root,
            instance_id=self.instance_id,
            node_tag=self.node_tag,
            bucket=bucket,
            domain=DOMAIN,
            global_scope=self.global_scope,
            subpath=subpath,
        )

    def path(self, bucket: str, subpath: str | list[str] | tuple[str, ...], file_name: str) -> Path:
        return self.dir(bucket, subpath) / file_name

    def write_json(self, bucket: str, subpath: str | list[str] | tuple[str, ...], file_name: str, obj: object) -> Path:
        path = self.path(bucket, subpath, file_name)
        self.node_ctx.write_json_atomic(path, obj)
        return path

    def read_json(self, bucket: str, subpath: str | list[str] | tuple[str, ...], file_name: str, default: Any = None) -> Any:
        path = self.path(bucket, subpath, file_name)
        if not path.exists():
            return default
        return self.node_ctx.read_json(path)

    def list_records(self, bucket: str, subpath: str | list[str] | tuple[str, ...]) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for path in self.node_ctx.list_files(self.dir(bucket, subpath), suffix=".json"):
            value = self.node_ctx.read_json(path)
            if isinstance(value, dict):
                records.append(value)
        return sorted(records, key=lambda item: str(item.get("created_at") or item.get("id") or ""))

    def append_event(self, kind: str, extra: dict[str, Any] | None = None, *, roh: bool = False) -> None:
        self.node_ctx.log_event(
            root=self.root,
            instance_id=self.instance_id,
            node_tag=self.node_tag,
            global_scope=self.global_scope,
            domain=DOMAIN,
            kind=kind,
            file_name="roh.actions.jsonl" if roh else "liferpg.events.jsonl",
            extra=extra or {},
        )

    def read_event_log(self, *, roh: bool = False) -> list[dict[str, Any]]:
        path = self.node_ctx.build_log_path(
            root=self.root,
            instance_id=self.instance_id,
            node_tag=self.node_tag,
            global_scope=self.global_scope,
            domain=DOMAIN,
            file_name="roh.actions.jsonl" if roh else "liferpg.events.jsonl",
        )
        if not path.exists():
            return []
        return [record for record in self.node_ctx.read_jsonl(path) if isinstance(record, dict)]


def store_from_ctx(ctx: Any) -> LifeRPGStore:
    return LifeRPGStore(
        root=Path(ctx.root),
        instance_id=getattr(ctx, "instance_id", "main") or "main",
        node_tag=getattr(ctx, "node_tag", None),
        global_scope=True,
    )
