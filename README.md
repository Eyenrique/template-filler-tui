# Template Filler TUI

TUI for filling placeholder-based prompt templates from the Tailoring Methodology.

## How to Run

```bash
# Navigate to the project directory
cd "/Users/enrique/Documents/Software Development/template-filler-tui"

# Activate the virtual environment (once per terminal session)
source .venv/bin/activate

# Run the TUI
python -m template_filler_tui
```

The `source .venv/bin/activate` command activates Python 3.12 with Textual installed. You only need to run it once per terminal window — after that, just repeat `python -m template_filler_tui` to relaunch.

## .gitignore

The `.gitignore` must include Python-specific entries to avoid committing thousands of generated files (the `.venv/` directory alone contains 2000+ files). Without these entries, git tracks the entire virtual environment and build artifacts, bloating the repository with files that should be recreated locally.

It excludes OS files, IDE files, and Python-specific artifacts:

- `.venv/` — the virtual environment (not committed; recreate with `python3.12 -m venv .venv && pip install -e .`)
- `__pycache__/`, `*.py[cod]` — Python bytecode cache
- `*.egg-info/`, `dist/`, `build/` — packaging artifacts
