"""Bundle the project's code into one Markdown file for sharing with an AI assistant.

Only files tracked by git are included (via `git ls-files`), so anything in
.gitignore -- .env, .token_cache.json, pipeline.log, .venv/ -- is left out
automatically. Run from the project root:

    python make_context.py

Then upload the generated context_bundle.md. Add context_bundle.md to .gitignore.
"""
import subprocess
from pathlib import Path

OUTPUT = Path("context_bundle.md")
INCLUDE = {".py": "python", ".sql": "sql", ".md": "markdown", ".yml": "yaml",
           ".yaml": "yaml", ".bat": "bat", ".txt": "text", ".toml": "toml"}
NEVER_INCLUDE = {".env", ".token_cache.json", OUTPUT.name}

tracked = subprocess.run(
    ["git", "ls-files"], capture_output=True, text=True, check=True
).stdout.splitlines()

sections = []
for name in sorted(tracked):
    path = Path(name)
    lang = INCLUDE.get(path.suffix.lower())
    if lang is None or path.name in NEVER_INCLUDE:
        continue
    content = path.read_text(encoding="utf-8", errors="replace")
    # Four backticks, so files that themselves contain ``` don't break the fence
    sections.append(f"## `{name}`\n\n````{lang}\n{content.rstrip()}\n````\n")

header = "# Project code snapshot\n\nGenerated from git-tracked files only.\n\n"
OUTPUT.write_text(header + "\n".join(sections), encoding="utf-8")
print(f"Wrote {OUTPUT} containing {len(sections)} files")
