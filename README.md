# prgen

**AI-powered commit message generator with persistent PR/MR notes tracking**

`prgen` is a CLI tool that automatically generates detailed commit messages using Google Gemini AI and maintains a running log of PR/MR-level information in a protected local file outside your repository.

---

## Features

- ✅ **Auto-generated commit messages** via git hook (runs on every `git commit`)
- ✅ **Persistent PR/MR notes** stored locally at `~/.prgen/notes/<repo-name>/<branch>.md`
- ✅ **Protected storage** (files created with `600` permissions)
- ✅ **Gemini AI integration** (free tier supported)
- ✅ **Per-branch tracking** (separate notes file for each branch)
- ✅ **Manual or automatic** workflow (CLI command or git hook)

---

## Installation

### 1. Install the package

```bash
cd /home/om-shivshankar/CascadeProjects/prgen
python -m pip install -e .
```

This installs the `prgen` command globally in your Python environment.

### 2. Set up your Gemini API key

Get a free API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

Add to your shell profile (`~/.bashrc` or `~/.zshrc`):

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Then reload:

```bash
source ~/.bashrc
```

**⚠️ Security note:** Keep your API key private. Consider using a secret manager instead of storing it in plaintext.

### 3. (Optional) Set a default model

```bash
export PRGEN_MODEL="models/gemini-1.5-pro"
```

If not set, the tool will use a sensible default.

---

## Usage

### Quick Start (Recommended Workflow)

1. **Install the git hook in your repo:**

   ```bash
   cd /path/to/your/repo
   prgen install-hook
   ```

2. **Make changes and stage them:**

   ```bash
   git add <files>
   ```

3. **Commit normally:**

   ```bash
   git commit
   ```

   The commit message will be **auto-generated** and the editor will open with it pre-filled.

4. **View accumulated PR notes:**

   ```bash
   cat ~/.prgen/notes/<repo-name>/<branch-name>.md
   ```

   Copy/paste this into your MR/PR description when ready.

---

## Commands

### `prgen install-hook`

Installs a `prepare-commit-msg` git hook in the current repository.

```bash
cd /path/to/your/repo
prgen install-hook
```

**Options:**
- `--force` - Overwrite existing hook if present

**What it does:**
- Creates `.git/hooks/prepare-commit-msg`
- Hook runs automatically on `git commit`
- Generates commit message from staged changes
- Appends PR notes to `~/.prgen/notes/<repo>/<branch>.md`

---

### `prgen gen`

Manually generate a commit message and PR notes.

```bash
prgen gen --staged
```

**Options:**
- `--staged` - Use staged changes (default)
- `--unstaged` - Use unstaged changes instead
- `--model <name>` - Override the model (e.g., `models/gemini-1.5-pro`)
- `--print` - Print to stdout only (don't write to file)
- `--write-message-file <path>` - Write commit message to a specific file

**What it does:**
- Reads git diff (staged or unstaged)
- Calls Gemini AI to generate commit message + PR notes
- Appends entry to `~/.prgen/notes/<repo>/<branch>.md`
- Prints commit message to stdout

---

### `prgen summary`

Generate a consolidated PR/MR description from all commits on the current branch.

```bash
prgen summary
```

**Options:**
- `--model <name>` - Override the model to use
- `--output <file>` - Write to file instead of stdout

**What it does:**
- Reads all accumulated PR notes for the current branch
- Uses AI to consolidate them into a single cohesive PR/MR description
- Outputs a ready-to-paste description with:
  - PR title
  - Summary of all changes
  - Consolidated testing notes
  - Risks and rollback strategy
  - Follow-up items

**Example:**
```bash
# Print to terminal
prgen summary

# Save to file
prgen summary --output pr-description.md
```

---

### `prgen list-models`

List available Gemini models for your API key.

```bash
prgen list-models
```

**What it does:**
- Queries the Gemini API
- Shows all models you can use
- Helpful for debugging quota/availability issues

---

### `prgen hook`

**Internal command** - called by the git hook. You don't need to run this manually.

---

## File Structure

### PR Notes Location

```
~/.prgen/
└── notes/
    └── <repo-name>/
        └── <branch-name>.md
```

**Example:**
```
~/.prgen/notes/soc_gen/feat-override.md
```

**Note:** Branch names with slashes (e.g., `feat/override`) are sanitized to use dashes (`feat-override`) in the filename to avoid creating nested directories.

### Notes File Format

Each entry in the notes file contains:

```markdown
---
_Generated: 2026-03-04T21:15:00_

### Commit message

```
Add vendor RDL override support

Implements support for vendor-provided RDL files via override.rdl
configuration in soc_yaml. Files can be specified with absolute or
relative paths and are copied to build_dir/rdl/.

Testing: Verified with sample vendor RDL files
```

### PR notes

## Summary

Added support for using vendor-provided RDL files instead of generating
them from register maps.

## Notable changes

- New override.rdl.path configuration in soc_yaml
- Supports both absolute and relative paths
- Automatic file copying to build directory

## Testing

- Tested with absolute path RDL files
- Tested with relative path RDL files
- Verified fallback to standard generation flow

## Risk/rollback

Low risk - only affects devices with override.rdl configured.
Rollback: remove override.rdl from device config.

## Follow-ups

- Add validation for RDL file format
- Document override.rdl schema in user guide
```

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Your Gemini API key (required) | - |
| `GOOGLE_API_KEY` | Alternative env var for API key | - |
| `PRGEN_MODEL` | Model to use for generation | Auto-detected |

### Per-Repo Hook Installation

The hook is installed **per repository**. You need to run `prgen install-hook` in each repo where you want auto-generated commit messages.

---

## Workflow Examples

### Example 1: Auto-commit with hook

```bash
# One-time setup per repo
cd ~/my-project
prgen install-hook

# Daily workflow
git add src/feature.py
git commit
# Editor opens with AI-generated message
# Save and close to commit
```

### Example 2: Preview before committing

```bash
git add src/feature.py
prgen gen --staged
# Review the generated message
git commit
# Message is auto-filled by hook
```

### Example 3: Manual commit message generation

```bash
git add src/feature.py
prgen gen --staged --write-message-file /tmp/commit.txt
cat /tmp/commit.txt
git commit -F /tmp/commit.txt
```

### Example 4: Create MR/PR description

After multiple commits on a branch:

```bash
# Generate consolidated PR description
prgen summary

# Or save to file and copy/paste
prgen summary --output pr-description.md
cat pr-description.md

# You can also view the raw accumulated notes
cat ~/.prgen/notes/my-project/feature-branch.md
```

---

## Troubleshooting

### "Missing GEMINI_API_KEY in environment"

**Solution:** Export your API key:
```bash
export GEMINI_API_KEY="your-key-here"
source ~/.bashrc
```

### "RESOURCE_EXHAUSTED" or quota errors

**Solution:** You've hit the free tier limit. Either:
- Wait for quota to reset (usually daily)
- Use a different model: `prgen list-models` to see available options
- Upgrade to a paid tier

### "models/gemini-X not found"

**Solution:** Check available models:
```bash
prgen list-models
```

Use the exact model name from the list:
```bash
prgen gen --staged --model "models/gemini-1.5-pro"
```

### Hook not running on commit

**Solution:**
1. Check hook exists: `ls -la .git/hooks/prepare-commit-msg`
2. Check it's executable: `chmod +x .git/hooks/prepare-commit-msg`
3. Reinstall: `prgen install-hook --force`

### Empty commit message generated

**Possible causes:**
- No staged changes: `git diff --staged` is empty
- API error (check terminal output)

**Solution:**
```bash
# Ensure you have staged changes
git status
git add <files>
prgen gen --staged
```

---

## Advanced Usage

### Custom model per command

```bash
prgen gen --staged --model "models/gemini-1.5-pro"
```

### Generate from unstaged changes

```bash
prgen gen --unstaged
```

### Print only (don't append to notes file)

```bash
prgen gen --staged --print
```

---

## How It Works

1. **On `git commit`** (with hook installed):
   - Hook reads staged diff via `git diff --staged`
   - Sends diff + git status + recent log to Gemini API
   - Gemini generates:
     - Commit message (title + body)
     - PR notes (summary, changes, testing, risks, follow-ups)
   - Commit message is written to `.git/COMMIT_EDITMSG`
   - PR notes are appended to `~/.prgen/notes/<repo>/<branch>.md`
   - Your editor opens with the pre-filled message

2. **Storage:**
   - Notes files are created with `600` permissions (owner read/write only)
   - One file per branch per repo
   - Files persist across commits
   - Located outside the repo (won't be committed accidentally)

3. **AI Prompt:**
   - Instructs Gemini to write conventional commit messages
   - Requests structured PR notes with specific sections
   - Includes context: diff, status, recent commits

---

## Security Considerations

- **API Key:** Store securely, never commit to git
- **Notes Files:** Created with `600` permissions (private to your user)
- **Diff Content:** Sent to Gemini API (don't use on proprietary code if concerned)
- **Local Storage:** Notes stored in `~/.prgen/notes/` (not in repo)

---

## Uninstallation

### Remove the hook from a repo

```bash
rm .git/hooks/prepare-commit-msg
```

### Uninstall the package

```bash
pip uninstall prgen
```

### Remove all notes

```bash
rm -rf ~/.prgen/notes/
```

---

## Contributing

This tool was created as a personal productivity tool. If you want to extend it:

1. Clone/fork the repo
2. Install in editable mode: `pip install -e .`
3. Make changes to `src/prgen/`
4. Test with `prgen` command

---

## License

MIT (or specify your license)

---

## FAQ

**Q: Can I use this with other AI providers (OpenAI, Anthropic, etc.)?**  
A: Currently only Gemini is supported. You can modify `src/prgen/gemini.py` to add other providers.

**Q: Will this work with merge commits?**  
A: The hook skips merge/squash commits to avoid interfering with git's default messages.

**Q: Can I customize the PR notes format?**  
A: Yes, edit the prompt in `src/prgen/gemini.py` (line ~17-33) to change the sections/format.

**Q: Does this work on Windows?**  
A: Should work, but paths will differ (`%USERPROFILE%\.prgen\notes\...`). Not tested.

**Q: Can I use this in CI/CD?**  
A: Not recommended - it's designed for interactive local commits. For CI, consider conventional commit linting instead.

**Q: What if I don't like the generated message?**  
A: Just edit it in your editor before saving. The hook only pre-fills; you have full control.

---

## Support

For issues or questions:
- Check the Troubleshooting section above
- Review Gemini API docs: https://ai.google.dev/gemini-api/docs
- Check your API quota: https://ai.dev/rate-limit

---

**Happy committing! 🚀**
