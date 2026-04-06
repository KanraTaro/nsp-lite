# NodeCTX

NodeCTX (Node Contextualizer) is a portable filesystem boundary layer for NSP-style systems.

It provides:

1. Canonical routing  
   All state is written to a predictable, validated directory structure.

2. Durable I/O  
   Writes are atomic and best-effort durable across crashes or power loss.

3. Filesystem boundary helpers  
   Common filesystem operations (read, list, delete, etc.) are centralized to avoid
   inconsistent or unsafe direct filesystem usage across systems.

---

## Philosophy

NodeCTX exists to make filesystem usage:

- predictable
- safe
- boring
- consistent across all systems

Higher-level systems should **prefer NodeCTX helpers over direct filesystem access**
for normal operations involving:

- state
- config
- workflow files
- logs
- queue-style processing

NodeCTX is not a framework.
It is a **contract for how systems touch the filesystem**.

---

## What NodeCTX does

### Canonical path routing

NodeCTX builds canonical state directories under:

State/<InstanceId>/<Scope>/<Domain>/<Bucket>/<Subpath...>/

Where:

- **Root**  
  Provided externally (typically via `ProjectRoot.get_effective_root()`)

- **InstanceId**  
  Logical instance name (example: `main`, `dev`, `prod`)

- **Scope**  
  - `Global` when `global_scope=True`
  - otherwise the node tag (`KanraDesktop`, `NodeA`, etc.)

- **Domain**  
  Subsystem grouping (`CLM`, `AutoRoh`, `RohTalk`, etc.)

- **Bucket**  
  High-level category (`Config`, `Data`, `Workflow`, `Logs`, etc.)

- **Subpath**  
  Optional nested segments (validated)

NodeCTX returns paths only.  
Directories are created by helpers when needed.

---

## Path safety rules

All routing segments (`instance_id`, `node_tag`, `domain`, `subpath`) are treated as **single folder names**.

Rules:

- must be non-empty
- must not contain path separators
- must not be `"."` or `".."` (prevents traversal)
- must not contain `":"` on Windows

Violations raise `ValueError`.

---

## Routing API

### build_state_dir


state_dir = build_state_dir(
    root=root,
    instance_id="main",
    node_tag="KanraDesktop",
    bucket="Data",
    domain="Example",
    global_scope=False,
    subpath="year/2026/month/01",
)


Result:

<Root>/State/main/KanraDesktop/Example/Data/year/2026/month/01/


---

## Bucket normalization

Known buckets are normalized to canonical casing:

* `"data"` → `Data`
* `"logs"` → `Logs`

Custom buckets are allowed and passed through unchanged.

Purpose:

* prevent path fragmentation
* avoid duplicate folders with different casing

---

## Filename prefixing (provenance only)

NodeCTX can prefix filenames to preserve origin:

Formats:

* `<node>-<filename>`
* `Global-<filename>`
* `<instance>-<node>-<filename>`
* `<instance>-Global-<filename>`

Prefixing:

* does **not** affect folder routing
* is strictly metadata/provenance

Helpers:

* `apply_prefix(...)`
* `strip_prefix(...)`
* `strip_prefix_base_name(...)`

---

## Environment variables

* `NODECTX_NODE_TAG`
* `NODECTX_INSTANCE_ID`
* `NODECTX_GLOBAL_TAG`
* `NODECTX_ENABLE_PREFIXING`
* `NODECTX_PREFIX_INSTANCE`

These control identity and prefixing behavior.

---

## Filesystem helpers

NodeCTX provides a consistent set of helpers so systems don’t need to use raw `Path` or `open()` for normal operations.

### Reads

* `read_json(path)`
* `read_text(path)`
* `read_bytes(path)`
* `read_jsonl(path)`

### Writes

* `write_json_atomic(path, obj)`
* `write_text_atomic(path, text)`
* `write_bytes_atomic(path, data)`
* `append_jsonl(path, obj)`

All writes:

* are atomic (write temp → replace)
* fsync file + parent directory (best effort)

---

## JSONL logging

### Basic

* `append_jsonl(path, obj)`

### Advanced

* `append_jsonl_rotating(...)`
* `log_event_jsonl(...)`
* `log_event(...)`
* `build_log_path(...)`

Features:

* rotation by size
* in-process throttling
* canonical log routing

---

## Filesystem inspection

* `exists(path)`
* `is_file(path)`
* `is_dir(path)`
* `list_dir(path)`
* `list_files(path, suffix=None)`

Behavior:

* `list_dir()` returns `[]` when missing
* raises if path exists but is not a directory
* results are sorted for deterministic behavior

---

## File mutation helpers

* `delete_file(path, missing_ok=True)`
* `atomic_replace(src, dst)`
* `atomic_move_to_dir(src, dst_dir, dst_name=None)`

Behavior:

* delete is file-only (raises on directories)
* atomic operations ensure safe moves and replaces
* parent directories are created automatically

---

## Directory helpers

* `ensure_dir(path)`
* `ensure_parent_dir(path)`

These ensure directory creation with best-effort durability.

---

## Design rules

* NodeCTX does not discover project roots
* NodeCTX does not encode business logic
* NodeCTX enforces structure, not meaning
* NodeCTX is safe to embed anywhere

---

## Usage guideline

If your code is doing something like:

* reading state files
* writing config
* appending logs
* listing workflow directories

You should probably be using NodeCTX.

If you find yourself writing:


Path(...).exists()
open(...)
os.replace(...)


in system-level code, it’s usually a sign that NodeCTX should expose that behavior instead.

---

## Tests

NodeCTX includes coverage for:

* routing correctness
* prefix behavior
* durable writes
* JSONL logging
* directory helpers
* filesystem inspection
* file mutation helpers

Run:


python run_tests.py


---

## Status

NodeCTX is stable and actively evolving.

It should be treated as the default filesystem contract for NSP systems.
