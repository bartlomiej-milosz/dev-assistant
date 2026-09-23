"""Read eligible blobs from an immutable Git snapshot and retain exact line coordinates."""

import re
import subprocess
import tomllib
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from urllib.parse import quote

SUFFIXES = {".java", ".py", ".sh", ".sql", ".md", ".toml", ".yaml", ".yml", ".xml", ".properties"}
SKIP_DIRS = {"target", "build", "dist", "vendor", "node_modules", ".venv"}
WINDOW = 20
OVERLAP = 5


@dataclass(frozen=True)
class Source:
    url: str
    branch: str

    @classmethod
    def read(cls, path: Path) -> "Source":
        with path.open("rb") as file:
            row = tomllib.load(file).get("repository", {})
        if not isinstance(row, dict):
            raise ValueError("Expected a [repository] table.")
        url, branch = row.get("url"), row.get("branch")
        if not isinstance(url, str) or not re.fullmatch(
            r"https://github\.com/[\w.-]+/[\w.-]+", url
        ):
            raise ValueError("Set repository.url to an HTTPS GitHub repository URL.")
        if not isinstance(branch, str) or not branch or branch.startswith("-"):
            raise ValueError("Set repository.branch to a branch name.")
        git("check-ref-format", "refs/heads/" + branch)
        return cls(url.removesuffix(".git"), branch)


@dataclass(frozen=True)
class Passage:
    path: str
    start: int
    end: int
    body: str

    def link(self, url: str, commit: str) -> str:
        return f"{url}/blob/{commit}/{quote(self.path)}#L{self.start}-L{self.end}"


def git(*args: str, cwd: Path | None = None) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, timeout=120
    ).stdout


def chunks(path: str, content: str) -> Iterator[Passage]:
    lines = content.splitlines()
    boundaries = [0]
    if path.lower().endswith(".md"):
        fence = ""
        for i, line in enumerate(lines):
            marker = re.match(r"^\s*(`{3,}|~{3,})", line)
            if marker:
                token = marker[1]
                if not fence:
                    fence = token
                elif token.startswith(fence):
                    fence = ""
            elif i and not fence and re.match(r"^#{1,6}\s", line):
                boundaries.append(i)
    boundaries.append(len(lines))
    for left, right in zip(boundaries, boundaries[1:]):
        for i in range(left, right, WINDOW - OVERLAP):
            end = min(i + WINDOW, right)
            body = "\n".join(lines[i:end])
            if body.strip():
                yield Passage(path, i + 1, end, body)
            if end == right:
                break


def read_tree(directory: Path, commit: str) -> Iterator[Passage]:
    for entry in git("ls-tree", "-rlz", commit, cwd=directory).split(b"\0"):
        if not entry:
            continue
        meta, name = entry.split(b"\t", 1)
        mode, _, oid, size = meta.split()
        if mode not in (b"100644", b"100755") or int(size) > 256_000:
            continue
        path = PurePosixPath(name.decode("utf-8", errors="replace"))
        if any(part.startswith(".") or part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in SUFFIXES and path.name not in {"Dockerfile", "Makefile"}:
            continue
        blob = git("cat-file", "blob", oid.decode(), cwd=directory)
        if b"\0" in blob:
            continue
        try:
            content = blob.decode()
        except UnicodeDecodeError:
            continue
        yield from chunks(str(path), content)


def snapshot(source: Source, revision: str | None = None) -> tuple[str, list[Passage]]:
    if revision is not None and not re.fullmatch("[0-9a-f]{40}", revision):
        raise ValueError("--commit expects a full 40-character Git SHA.")
    with TemporaryDirectory(prefix="dev-assistant-git-") as tmp:
        directory = Path(tmp)
        git("init", "--bare", "--quiet", cwd=directory)
        git(
            "fetch",
            "--depth=1",
            "--no-tags",
            "--",
            source.url,
            revision or f"refs/heads/{source.branch}",
            cwd=directory,
        )
        commit = git("rev-parse", "FETCH_HEAD^{commit}", cwd=directory).decode().strip()
        return commit, list(read_tree(directory, commit))
