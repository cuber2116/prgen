from __future__ import annotations

import datetime as _dt
import os
import re
from dataclasses import dataclass
from pathlib import Path

from prgen.git_tools import GitRepo


@dataclass(frozen=True)
class NotesStore:
    base_dir: Path

    @staticmethod
    def default() -> "NotesStore":
        home = Path.home()
        return NotesStore(base_dir=home / ".prgen" / "notes")

    @staticmethod
    def _sanitize_branch_name(branch: str) -> str:
        return branch.replace("/", "-").replace("\\", "-")

    def notes_path_for(self, *, repo: GitRepo) -> Path:
        repo_name = repo.get_repo_name()
        branch = self._sanitize_branch_name(repo.get_branch())
        return self.base_dir / repo_name / f"{branch}.md"

    def append_entry(self, *, repo: GitRepo, commit_message: str, pr_notes: str) -> Path:
        path = self.notes_path_for(repo=repo)
        path.parent.mkdir(parents=True, exist_ok=True)

        if not path.exists():
            path.write_text("", encoding="utf-8")
            os.chmod(path, 0o600)

        ts = _dt.datetime.now().isoformat(timespec="seconds")
        entry = (
            f"\n\n---\n"
            f"_Generated: {ts}_\n\n"
            f"### Commit message\n\n"
            f"```\n{commit_message.rstrip()}\n```\n\n"
            f"### PR notes\n\n"
            f"{pr_notes.rstrip()}\n"
        )

        with path.open("a", encoding="utf-8") as f:
            f.write(entry)

        return path

    def generate_summary(self, *, repo: GitRepo, api_key: str, model: str) -> str:
        from prgen.gemini import GeminiClient

        path = self.notes_path_for(repo=repo)
        if not path.exists():
            return "## Summary\n\nNo PR notes found for this branch.\n"

        content = path.read_text(encoding="utf-8")
        if not content.strip():
            return "## Summary\n\nNo PR notes found for this branch.\n"

        client = GeminiClient(api_key=api_key, model=model)
        prompt = (
            "You are a senior engineer writing a Pull Request / Merge Request description.\n"
            "Below are individual commit messages and PR notes from multiple commits on a branch.\n"
            "Your task: Create a single, cohesive PR/MR description that summarizes ALL the work.\n\n"
            "Output format (Markdown):\n"
            "# PR Title\n"
            "[Concise title summarizing all changes]\n\n"
            "## Summary\n"
            "[High-level overview of what this PR accomplishes]\n\n"
            "## Changes\n"
            "[Bullet list of key changes across all commits]\n\n"
            "## Testing\n"
            "[How this was tested, consolidated from all commits]\n\n"
            "## Risks & Rollback\n"
            "[Any risks and rollback strategy]\n\n"
            "## Follow-ups\n"
            "[Any follow-up work needed]\n\n"
            "---\n\n"
            "Individual commit notes:\n\n"
            f"{content}\n"
        )

        resp = client._generate_raw(prompt=prompt)
        return resp.strip() + "\n"
