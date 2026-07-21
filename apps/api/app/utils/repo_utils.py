"""Repository cloning and filesystem access.

Everything here handles **attacker-controlled input**: the URL comes straight
from a form, and file paths come from query strings. The previous version passed
both to `git.Repo.clone_from` and `os.path.join` with essentially no validation.

Three classes of problem this module exists to prevent:

1. **SSRF.** `git clone` accepts far more than https. `file:///etc/`,
   `git://internal-host/`, `ssh://…`, and `http://169.254.169.254/` (the cloud
   metadata endpoint) were all reachable by submitting them as a "GitHub URL".
2. **Resource exhaustion.** No depth limit, no size cap, no timeout, and no
   cleanup — a full clone of a large monorepo, kept forever under `/tmp`.
3. **Path traversal.** The old containment check was
   `full_path.startswith(repo_path)`, which is a *string* prefix test:
   `/tmp/reploai/<id>-evil` starts with `/tmp/reploai/<id>` and passed.
"""

import asyncio
import logging
import os
import shutil
import subprocess
import uuid
from pathlib import Path
from urllib.parse import urlparse

from ..core.exceptions import ExternalServiceError, InvalidInputError

logger = logging.getLogger(__name__)

CLONE_ROOT = Path("/tmp/reploai")

# Allowlist, not a blocklist. The product analyses public GitHub repositories, so
# anything else is a mistake or an attack — and a blocklist of "bad" hosts can
# never be complete (DNS rebinding, redirects, IPv6 forms of the same address).
ALLOWED_HOSTS = frozenset({"github.com", "www.github.com"})

CLONE_TIMEOUT_SECONDS = 120
MAX_REPO_BYTES = 500 * 1024 * 1024  # 500 MB
MAX_FILE_BYTES = 1024 * 1024  # 1 MB

# Absolute path, resolved once. Invoking bare "git" would resolve through $PATH
# at call time, so anything able to influence the environment could substitute a
# different binary. Resolved at import so a missing git fails at startup rather
# than on the first user request.
GIT_BINARY = shutil.which("git")


def normalise_repo_url(raw_url: str) -> str:
    """Validate and canonicalise a repository URL, or raise.

    Returns `https://github.com/{owner}/{repo}` with any `.git` suffix, trailing
    slash, query string, fragment, or embedded credentials removed.
    """
    url = (raw_url or "").strip()
    if not url:
        raise InvalidInputError("Repository URL is required.")

    parsed = urlparse(url)

    # Scheme first: this is what blocks file://, git://, ssh://, and scp-style
    # `git@github.com:owner/repo` (which urlparse sees as scheme-less).
    if parsed.scheme != "https":
        raise InvalidInputError("Repository URL must start with https://")

    # `user:pass@host` — reject rather than honour. Credentials in a URL are
    # either a mistake or an attempt to make the host look like something else.
    if parsed.username or parsed.password:
        raise InvalidInputError("Repository URL must not contain credentials.")

    host = (parsed.hostname or "").lower()
    if host not in ALLOWED_HOSTS:
        raise InvalidInputError("Only public github.com repositories are supported.")

    if parsed.port is not None:
        raise InvalidInputError("Repository URL must not specify a port.")

    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) != 2:
        raise InvalidInputError("Repository URL must be of the form https://github.com/owner/repo")

    owner, repo = parts
    if repo.endswith(".git"):
        repo = repo[: -len(".git")]

    # Owner/repo charset per GitHub's own rules. Also stops `..` from ever
    # reaching a path.
    for segment in (owner, repo):
        if not segment or segment in {".", ".."}:
            raise InvalidInputError("Repository URL contains an invalid path segment.")
        if not all(c.isalnum() or c in "-._" for c in segment):
            raise InvalidInputError("Repository URL contains invalid characters.")

    return f"https://github.com/{owner}/{repo}"


def repo_name_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


def get_repo_path(repo_id: uuid.UUID) -> Path:
    return CLONE_ROOT / str(repo_id)


def safe_join(base: Path, relative: str) -> Path:
    """Resolve `relative` under `base`, or raise.

    Uses `Path.resolve()` + `is_relative_to` rather than a string prefix test, so
    `..` segments, absolute paths, and symlinks pointing outside the tree are all
    rejected. `strict=False` because the target may legitimately not exist.
    """
    if os.path.isabs(relative):
        raise InvalidInputError("File path must be relative to the repository root.")

    base_resolved = base.resolve()
    target = (base_resolved / relative).resolve(strict=False)

    if not target.is_relative_to(base_resolved):
        raise InvalidInputError("File path escapes the repository root.")

    return target


def _clone_blocking(url: str, dest: Path) -> None:
    """Run `git clone` as a subprocess with a hard timeout.

    Deliberately not GitPython: it offers no reliable timeout, so a hung clone
    against a slow or malicious host held a worker forever.

    `--depth 1 --single-branch` fetches one commit of one branch. Full history is
    never used — the pipeline reads the working tree — and it is the difference
    between megabytes and gigabytes on a large repository.
    """
    if GIT_BINARY is None:
        raise ExternalServiceError("git is not installed on this host.")

    dest.parent.mkdir(parents=True, exist_ok=True)

    env = {
        **os.environ,
        # Never let git prompt for credentials: on a private repo it would
        # otherwise block until the timeout instead of failing immediately.
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_ASKPASS": "",
        "GCM_INTERACTIVE": "never",
    }

    try:
        subprocess.run(  # noqa: S603 - url is validated by normalise_repo_url
            [
                GIT_BINARY,
                "clone",
                "--depth",
                "1",
                "--single-branch",
                "--no-tags",
                # Refuse repo-supplied hooks that execute on clone.
                "--config",
                "core.hooksPath=/dev/null",
                url,
                str(dest),
            ],
            check=True,
            capture_output=True,
            timeout=CLONE_TIMEOUT_SECONDS,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        shutil.rmtree(dest, ignore_errors=True)
        raise ExternalServiceError(f"Cloning timed out after {CLONE_TIMEOUT_SECONDS}s.") from exc
    except subprocess.CalledProcessError as exc:
        shutil.rmtree(dest, ignore_errors=True)
        # git writes the attempted URL into stderr; surfacing it verbatim would
        # echo attacker input back to the client.
        stderr = (exc.stderr or b"").decode("utf-8", "ignore")
        if "not found" in stderr.lower():
            raise InvalidInputError(
                "Repository not found. It may be private or may not exist."
            ) from exc
        logger.warning("git clone failed for %s: %s", url, stderr[:500])
        raise ExternalServiceError("Could not clone the repository.") from exc


def _directory_size(path: Path) -> int:
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            fp = Path(root) / name
            if not fp.is_symlink():
                try:
                    total += fp.stat().st_size
                except OSError:
                    continue
    return total


async def clone_repository(url: str, repo_id: uuid.UUID, *, force: bool = False) -> Path:
    """Clone a validated repository URL. Returns the local path.

    Runs in a worker thread: `git clone` is blocking and can take a minute, which
    inside `async def` would stall the entire event loop — every other request on
    the process included.
    """
    dest = get_repo_path(repo_id)

    if dest.exists():
        if not force:
            return dest
        await asyncio.to_thread(shutil.rmtree, dest, True)

    await asyncio.to_thread(_clone_blocking, url, dest)

    size = await asyncio.to_thread(_directory_size, dest)
    if size > MAX_REPO_BYTES:
        # Checked after the fact: git offers no reliable pre-flight size limit,
        # and --depth 1 already bounds the common case. This catches the rest
        # rather than letting one repository fill the disk.
        await asyncio.to_thread(shutil.rmtree, dest, True)
        raise InvalidInputError(
            f"Repository is too large ({size // (1024 * 1024)} MB, limit "
            f"{MAX_REPO_BYTES // (1024 * 1024)} MB)."
        )

    return dest


async def remove_clone(repo_id: uuid.UUID) -> None:
    """Delete a clone. Nothing called this before, so `/tmp/reploai` grew without
    bound until the disk filled."""
    await asyncio.to_thread(shutil.rmtree, get_repo_path(repo_id), True)


def build_file_tree(
    repo_path: Path | str,
    current_path: str = "",
    max_depth: int = 10,
    current_depth: int = 0,
) -> list[dict]:
    """Walk the working tree, skipping vendored and build directories."""
    repo_path = Path(repo_path)
    if current_depth >= max_depth or not repo_path.exists():
        return []

    ignored_dirs = {
        ".git",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        "dist",
        "build",
        ".next",
        ".cache",
        ".turbo",
        "target",
        "vendor",
    }
    code_extensions = {
        ".js", ".jsx", ".ts", ".tsx", ".py", ".java", ".cpp", ".c", ".h", ".go",
        ".rs", ".rb", ".php", ".cs", ".kt", ".swift", ".scala", ".json", ".md",
        ".yml", ".yaml", ".toml", ".html", ".css", ".scss", ".less", ".sh",
        ".bash", ".zsh", ".sql", ".xml", ".txt", ".ini", ".conf",
    }  # fmt: skip

    tree: list[dict] = []
    try:
        for item in sorted(os.listdir(repo_path)):
            if item.startswith("."):
                continue

            item_path = repo_path / item
            rel_path = f"{current_path}/{item}" if current_path else item

            # Never follow symlinks: a repo can contain one pointing at /etc,
            # and walking it would expose host files through the file endpoint.
            if item_path.is_symlink():
                continue

            if item_path.is_dir():
                if item in ignored_dirs:
                    continue
                children = build_file_tree(item_path, rel_path, max_depth, current_depth + 1)
                tree.append(
                    {
                        "name": item,
                        "path": rel_path,
                        "type": "directory",
                        "children": children or None,
                    }
                )
            elif item_path.is_file() and (
                item_path.suffix.lower() in code_extensions or not item_path.suffix
            ):
                tree.append({"name": item, "path": rel_path, "type": "file", "children": None})
    except PermissionError:
        logger.debug("Permission denied walking %s", repo_path)
    except OSError as exc:
        # Was a bare `except Exception: pass`, so a real failure looked like an
        # empty directory.
        logger.warning("Error walking %s: %s", repo_path, exc)

    return tree


def read_file(repo_path: Path, relative_path: str) -> tuple[str, int]:
    """Read one file from a clone. Returns `(content, size)`."""
    target = safe_join(repo_path, relative_path)

    if target.is_symlink():
        raise InvalidInputError("Refusing to read a symlink.")
    if not target.is_file():
        raise InvalidInputError("File not found.")

    size = target.stat().st_size
    if size > MAX_FILE_BYTES:
        raise InvalidInputError(
            f"File is too large ({size // 1024} KB, limit {MAX_FILE_BYTES // 1024} KB)."
        )

    return target.read_text(encoding="utf-8", errors="ignore"), size
