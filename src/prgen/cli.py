import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from prgen.git_tools import GitRepo
from prgen.notes import NotesStore


@dataclass(frozen=True)
class GenerateOptions:
    use_staged: bool
    model: str


def _run(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="prgen")
    sub = parser.add_subparsers(dest="cmd", required=True)

    gen = sub.add_parser("gen")
    gen.add_argument("--staged", action="store_true", default=False)
    gen.add_argument("--unstaged", action="store_true", default=False)
    gen.add_argument("--model", default=os.environ.get("PRGEN_MODEL", "gemini-1.5-flash"))
    gen.add_argument("--print", action="store_true", default=False)
    gen.add_argument("--write-message-file", default=None)

    hook = sub.add_parser("hook")
    hook.add_argument("message_file")
    hook.add_argument("source", nargs="?", default="")
    hook.add_argument("sha", nargs="?", default="")
    hook.add_argument("--model", default=os.environ.get("PRGEN_MODEL", "gemini-1.5-flash"))

    install = sub.add_parser("install-hook")
    install.add_argument("--force", action="store_true", default=False)

    list_models = sub.add_parser("list-models")

    summary = sub.add_parser("summary")
    summary.add_argument("--model", default=os.environ.get("PRGEN_MODEL", "gemini-1.5-flash"))
    summary.add_argument("--output", default=None, help="Write to file instead of stdout")

    args = parser.parse_args(argv)

    if args.cmd == "list-models":
        from prgen.gemini import list_available_models
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise SystemExit("Missing GEMINI_API_KEY (or GOOGLE_API_KEY) in environment")
        list_available_models(api_key)
        return 0

    if args.cmd == "summary":
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise SystemExit("Missing GEMINI_API_KEY (or GOOGLE_API_KEY) in environment")
        
        repo = GitRepo.open_from_cwd()
        notes = NotesStore.default()
        summary_text = notes.generate_summary(repo=repo, api_key=api_key, model=args.model)
        
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(summary_text, encoding="utf-8")
            sys.stdout.write(f"Summary written to {output_path}\n")
        else:
            sys.stdout.write(summary_text)
        
        return 0

    if args.cmd == "install-hook":
        repo = GitRepo.open_from_cwd()
        repo.install_prepare_commit_msg_hook(force=args.force)
        return 0

    if args.cmd == "hook":
        if args.source in {"merge", "squash", "commit"}:
            return 0

        message_file = Path(args.message_file)
        try:
            existing = message_file.read_text(encoding="utf-8")
        except FileNotFoundError:
            existing = ""

        non_comment_lines = [
            line for line in existing.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        if non_comment_lines:
            return 0

        repo = GitRepo.open_from_cwd()
        return _generate_and_write(
            repo=repo,
            model=args.model,
            use_staged=True,
            print_only=False,
            message_file=message_file,
        )

    if args.cmd == "gen":
        if args.staged and args.unstaged:
            raise SystemExit("Choose at most one of --staged/--unstaged")

        use_staged = True
        if args.unstaged:
            use_staged = False

        repo = GitRepo.open_from_cwd()
        message_file = Path(args.write_message_file) if args.write_message_file else None
        return _generate_and_write(
            repo=repo,
            model=args.model,
            use_staged=use_staged,
            print_only=args.print,
            message_file=message_file,
        )

    return 2


def _generate_and_write(
    *,
    repo: GitRepo,
    model: str,
    use_staged: bool,
    print_only: bool,
    message_file: Path | None,
) -> int:
    from prgen.gemini import GeminiClient

    diff = repo.get_diff(staged=use_staged)
    if not diff.strip():
        return 0

    status = repo.get_status_porcelain()
    recent = repo.get_recent_log(max_count=15)

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise SystemExit("Missing GEMINI_API_KEY (or GOOGLE_API_KEY) in environment")

    client = GeminiClient(api_key=api_key, model=model)
    commit_message, pr_notes = client.generate(diff=diff, status=status, recent_log=recent)

    notes = NotesStore.default()
    notes_path = notes.append_entry(repo=repo, commit_message=commit_message, pr_notes=pr_notes)

    if message_file is not None:
        message_file.write_text(commit_message.rstrip() + "\n", encoding="utf-8")

    if print_only or message_file is None:
        sys.stdout.write(commit_message.rstrip() + "\n")
        sys.stdout.write("\n")
        sys.stdout.write(str(notes_path) + "\n")

    return 0


def main() -> None:
    try:
        raise SystemExit(_run(sys.argv[1:]))
    except subprocess.CalledProcessError as e:
        if e.stdout:
            sys.stdout.write(e.stdout)
        if e.stderr:
            sys.stderr.write(e.stderr)
        raise SystemExit(e.returncode)
