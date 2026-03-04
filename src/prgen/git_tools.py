import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GitRepo:
    root: Path

    @staticmethod
    def open_from_cwd() -> "GitRepo":
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.STDOUT,
            text=True,
        ).strip()
        return GitRepo(root=Path(out))

    def _git(self, *args: str) -> str:
        return subprocess.check_output(
            ["git", *args],
            cwd=str(self.root),
            stderr=subprocess.STDOUT,
            text=True,
        )

    def get_branch(self) -> str:
        return self._git("rev-parse", "--abbrev-ref", "HEAD").strip()

    def get_repo_name(self) -> str:
        return self.root.name

    def get_status_porcelain(self) -> str:
        return self._git("status", "--porcelain=v1")

    def get_diff(self, *, staged: bool) -> str:
        if staged:
            return self._git("diff", "--staged")
        return self._git("diff")

    def get_recent_log(self, *, max_count: int) -> str:
        return self._git("log", f"-{max_count}", "--oneline", "--decorate")

    def install_prepare_commit_msg_hook(self, *, force: bool) -> None:
        hooks_dir = self.root / ".git" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        hook_path = hooks_dir / "prepare-commit-msg"

        if hook_path.exists() and not force:
            raise SystemExit(f"Hook already exists at {hook_path}. Re-run with --force to overwrite")

        content = "\n".join(
            [
                "#!/usr/bin/env sh",
                "set -e",
                "if command -v prgen >/dev/null 2>&1; then",
                "  prgen hook \"$1\" \"$2\" \"$3\" || true",
                "fi",
                "",
            ]
        )
        hook_path.write_text(content, encoding="utf-8")
        os.chmod(hook_path, 0o755)
