# ProjectRoot (V1)

ProjectRoot is a tiny, portable utility for discovering a project's logical root directory at runtime.

It performs a bounded upward search from a starting directory, looking for:
1. A **root marker file** (default: `.root`)
2. One or more **anchor files** (default: `kontainer.json`)

ProjectRoot does **not** write to disk, does **not** require NSP, and does **not** assume any project name or folder structure. It only reads the filesystem and logs what it found.

This module exists so other systems (like NodeCTX) can route paths under a stable root without hardcoding paths.

## Public API

### `find_root(start_dir: Path, marker: str, anchors: Iterable[str], max_depth: int) -> Optional[Path]`

Search upward from `start_dir` until it finds a directory that contains:
- `marker`, OR
- any file listed in `anchors`

Stops when:
- a match is found, OR
- `max_depth` parent traversals are done, OR
- the filesystem root is reached

Returns:
- the discovered root directory as a `Path`, or
- `None` if not found

---

### `get_effective_root(start_dir: Optional[Path] = None) -> Path`

Convenience wrapper around `find_root()` that reads defaults from environment variables.

Returns:
- the discovered root directory as a `Path`
- if nothing is found within search limits, returns the starting directory and emits a warning


## Configuration (Environment Variables)

### `RR_ROOT_MARKER`
Default: `.root`  
A filename that explicitly marks a directory as the root. If set to empty/white-space, marker checks are disabled (anchors still apply).

### `RR_ANCHOR_FILES`
Default: `kontainer.json`  
Comma-separated list of anchor filenames that can act as root signals if `.root` is not present.

Example:
- `RR_ANCHOR_FILES="kontainer.json,pyproject.toml,.git"`

### `RR_MAX_DEPTH`
Default: `25`  
Maximum number of parent directories to traverse upward before giving up. Negative values are treated as 0.

### `RR_START_DIR`
Default: unset  
Optional override for the starting directory used by `get_effective_root()` when `start_dir` is not passed.
If unset, `get_effective_root()` uses the current working directory.


## Typical Usage

### Minimal usage
```python
from ProjectRoot.skill import get_effective_root

root = get_effective_root()
print(root)

