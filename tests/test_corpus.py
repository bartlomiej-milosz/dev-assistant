import subprocess
from pathlib import Path

import pytest

from dev_assistant.corpus import Passage, Source, chunks, snapshot


def test_windows_preserve_lines_and_do_not_repeat_tail():
    parts = list(chunks("A.java", "\n".join(str(i) for i in range(1, 36))))
    assert [(p.start, p.end) for p in parts] == [(1, 20), (16, 35)]
    assert parts[1].body.splitlines()[0] == "16"


def test_markdown_headings_in_fences_are_content():
    text = "# First\n```sh\n# comment\n```\n## Next\nanswer"
    assert [(p.start, p.end) for p in chunks("README.md", text)] == [(1, 4), (5, 6)]
    assert list(chunks("empty.py", " \n")) == []
    assert Passage("a b.py", 1, 2, "x").link("url", "abc") == "url/blob/abc/a%20b.py#L1-L2"


def test_fetch_uses_committed_files_only(tmp_path: Path):
    def git(*args):
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)

    git("init", "-b", "main")
    (tmp_path / "source.py").write_text("original = True")
    (tmp_path / ".env").write_text("ignored")
    (tmp_path / "alias.py").symlink_to("source.py")
    git("add", ".")
    git("-c", "user.email=test@example.org", "-c", "user.name=Test", "commit", "-m", "fixture")
    (tmp_path / "source.py").write_text("uncommitted")
    commit, passages = snapshot(Source(str(tmp_path), "main"))
    assert passages == [Passage("source.py", 1, 1, "original = True")]
    assert snapshot(Source(str(tmp_path), "main"), commit) == (commit, passages)


@pytest.mark.parametrize("url", ["file:///tmp/repo", "ext::cmd", "https://token@github.com/a/b"])
def test_config_requires_plain_github_url(tmp_path, url):
    path = tmp_path / "source.toml"
    path.write_text(f'[repository]\nurl="{url}"\nbranch="main"')
    with pytest.raises(ValueError):
        Source.read(path)
