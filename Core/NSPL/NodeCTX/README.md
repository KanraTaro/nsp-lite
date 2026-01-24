# NodeCTX

NodeCTX (Node Contextualizer) is a small, portable routing and durable I/O layer.

It solves two recurring problems:

1. Canonical routing  
   Every system saves state in the same predictable folder structure.

2. Durable writes  
   Writes are atomic and best-effort durable across crashes or power loss.

NodeCTX does not discover the project root.
Pair it with ProjectRoot for root discovery.

---

## What NodeCTX does

### Canonical path routing

NodeCTX builds canonical state directories under:

~~~
State/<InstanceId>/<Scope>/<Bucket>/<Domain>/<Subpath...>/
~~~

Where:

- Root  
  Provided by ProjectRoot.get_effective_root()

- InstanceId  
  Logical instance name (for example: main, dev, prod)

- Scope  
  Global when global_scope=True  
  Otherwise the node tag (for example: KanraDesktop, MediaNodeA)

- Bucket  
  High-level category (Config, Data, Workflow, Logs, etc)

- Domain  
  Subsystem grouping (CLM, AutoRoh, RohTalk, etc)

- Subpath  
  Optional nested path for organization. Subpath may be a slash-separated string or a list of segments; each segment is validated.

NodeCTX returns paths only.
Directories are created by write helpers as needed.

---

## Path segment safety rules

NodeCTX treats `instance_id`, `node_tag`, `domain`, and each `subpath` segment as **single folder names**.

To prevent path traversal and cross-platform weirdness:

- Segments must be non-empty after trimming whitespace
- Segments must not contain path separators (`/` or platform separators)
- Segments must not be `"."` or `".."` (prevents traversal)
- On Windows (`os.name == "nt"`), segments must not contain `":"` (drive letters / ADS hazards)

If a value violates these rules, NodeCTX raises `ValueError`.

---

## Routing API

### build_state_dir

Example usage:
~~~
	from pathlib import Path
	
    from Core.NSPL.NodeCTX import build_state_dir
    from Core.NSPL.ProjectRoot import get_effective_root
	
	root: Path = get_effective_root()
	
	state_dir: Path = build_state_dir(
	    root=root,
	    instance_id="main",
	    node_tag="KanraDesktop",
	    bucket="Data",
	    domain="Example",
	    global_scope=False,
	    subpath="year/2026/month/01"
	)
~~~
Result:
~~~
<Root>/State/main/KanraDesktop/Data/Example/year/2026/month/01/
~~~
___

## Bucket normalization

NodeCTX normalizes known buckets to prevent path fragmentation.

Examples:

- "data", "DATA", "Data" → Data
- "logs", "LOGS" → Logs

Custom buckets are allowed and passed through unchanged.

Bucket normalization is not enforcement.
It prevents accidental duplication like having both:

data/
Data/

Rules:

- bucket must be non-empty
- bucket must not contain path separators
- custom buckets are allowed

---

## Filename prefixing (provenance only)

NodeCTX can prefix filenames to preserve provenance when files leave the system.

Supported formats:
~~~
- <node>-<filename>
- Global-<filename>
- <instance>-<node>-<filename>
- <instance>-Global-<filename>
~~~
Prefixing never affects routing.
Folder layout remains canonical.

Prefix stripping helpers are provided for re-ingestion.

**Note:** the global prefix tag defaults to `Global` but can be overridden via `NODECTX_GLOBAL_TAG`.

---

## Durable writes

NodeCTX provides helpers for durable file output:

- Atomic JSON writes
- Pretty-printed JSON with newline termination
- JSONL append with flush and fsync

Durability goals:

- Never corrupt an existing file
- Minimize data loss on crash
- Prefer correctness over performance

---

## Design rules

- NodeCTX never discovers project roots
- NodeCTX never hardcodes NSP concepts
- NodeCTX enforces shape, not meaning
- NodeCTX is safe to embed in any repository

---

## Tests

NodeCTX ships with unittest coverage for:

- Bucket normalization
- Global vs local routing
- Subpath handling (string and list)
- Prefix application and stripping
- Durable JSON writes
- JSONL append correctness

Run tests from repo root:
~~~
python run_tests.py
~~~
---

## Status

NodeCTX V1 is complete and stable.

Future systems should treat NodeCTX as foundational,
in the same way filesystems treat open() and fsync().

You do not think about it.
You trust it.

---

## What to do next (optional)

- Commit this file alongside passing tests
- Add a lightweight metadata header to node_ctx.py later
- Integrate NodeCTX + ProjectRoot into a real system (CLM or RohTalk)

This layer is done.
