from __future__ import annotations

import re
import sys
from dataclasses import dataclass

from google import genai


def list_available_models(api_key: str) -> None:
    client = genai.Client(api_key=api_key, http_options={'api_version': 'v1'})
    try:
        models = client.models.list()
        sys.stdout.write("Available models:\n")
        for model in models:
            name = getattr(model, 'name', str(model))
            sys.stdout.write(f"  - {name}\n")
    except Exception as e:
        sys.stderr.write(f"Error listing models: {e}\n")
        raise SystemExit(1)


@dataclass
class GeminiClient:
    api_key: str
    model: str

    def _generate_raw(self, *, prompt: str) -> str:
        client = genai.Client(
            api_key=self.api_key,
            http_options={'api_version': 'v1'}
        )
        resp = client.models.generate_content(model=self.model, contents=prompt)
        return getattr(resp, "text", None) or ""

    def generate(self, *, diff: str, status: str, recent_log: str) -> tuple[str, str]:
        client = genai.Client(
            api_key=self.api_key,
            http_options={'api_version': 'v1'}
        )

        prompt = (
            "You are a senior engineer. Generate a high-quality git commit message and PR notes.\n"
            "Return output in exactly this format:\n"
            "<COMMIT_MESSAGE>\n"
            "...\n"
            "</COMMIT_MESSAGE>\n"
            "<PR_NOTES>\n"
            "...\n"
            "</PR_NOTES>\n\n"
            "Rules for COMMIT_MESSAGE:\n"
            "- First line: concise imperative title <= 72 chars\n"
            "- Blank line after title\n"
            "- Body: wrap at ~100 chars, explain what/why, mention behavior changes\n"
            "- Include Testing section if possible\n"
            "Rules for PR_NOTES:\n"
            "- Markdown\n"
            "- Include: Summary, Notable changes, Testing, Risk/rollback, Follow-ups\n\n"
            "Context:\n"
            f"GIT_STATUS_PORCELAIN:\n{status}\n\n"
            f"RECENT_LOG:\n{recent_log}\n\n"
            f"DIFF:\n{diff}\n"
        )

        resp = client.models.generate_content(model=self.model, contents=prompt)
        text = getattr(resp, "text", None) or ""

        commit = _extract_tag(text, "COMMIT_MESSAGE")
        notes = _extract_tag(text, "PR_NOTES")

        if not commit.strip():
            commit = "Update code\n\nGenerated commit message unavailable.\n"
        if not notes.strip():
            notes = "## Summary\n\nGenerated PR notes unavailable.\n"

        commit = _normalize_commit_message(commit)
        notes = notes.strip() + "\n"

        return commit, notes


def _extract_tag(text: str, tag: str) -> str:
    m = re.search(rf"<{tag}>(.*?)</{tag}>", text, flags=re.DOTALL | re.IGNORECASE)
    if not m:
        return ""
    return m.group(1).strip("\n")


def _normalize_commit_message(msg: str) -> str:
    msg = msg.strip("\n")
    lines = msg.splitlines()
    if not lines:
        return ""

    title = lines[0].strip()
    body_lines = [l.rstrip() for l in lines[1:]]

    if title and len(title) > 72:
        title = title[:72].rstrip()

    while body_lines and body_lines[0].strip() == "":
        body_lines.pop(0)

    out = [title]
    if body_lines:
        out.append("")
        out.extend(body_lines)

    return "\n".join(out).rstrip() + "\n"
