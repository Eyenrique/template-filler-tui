#!/usr/bin/env python3
"""
Template Filler — extracts prompt templates from the Tailoring Methodology,
fills placeholders interactively, verifies completeness, and copies to clipboard.
"""

import re
import json
import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass, field

# ── Configuration ──────────────────────────────────────────────────────────────

METHODOLOGY_PATH = Path(
    "/Users/enrique/Documents/Software Development/dev-workflow/"
    "dev-workflowWF/docs/Tailoring Methodology/State Capture/"
    "Tailoring_Methodology_state_capture.md"
)

MEMORY_FILE = Path.home() / ".template_filler_memory.json"

# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class Template:
    """A single code-block template from the methodology."""
    label: str          # e.g., "If AI only read questionnaire file (common case)"
    text: str           # the raw template text inside the code block


@dataclass
class Turn:
    """A turn within a step (Turn 1, Turn 2, …)."""
    number: str         # e.g., "1", "2"
    title: str          # e.g., "Initial Understanding"
    templates: list     # list of Template objects


@dataclass
class Step:
    """A step (or sub-step) in the methodology."""
    id: str             # e.g., "3.1.1", "6.1", "8"
    title: str          # e.g., "Golden Methodology Prompt Generator"
    turns: list = field(default_factory=list)        # list of Turn objects
    standalone_templates: list = field(default_factory=list)  # templates not inside a turn


# ── Parsing ────────────────────────────────────────────────────────────────────

def parse_methodology(path: Path) -> list:
    """Parse the methodology markdown into a list of Step objects."""
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")

    steps = []
    current_step = None
    current_turn = None
    in_how_framed = False        # saw "How this was framed:" heading
    in_code_block = False
    code_block_lines = []
    variant_label = ""
    pending_variant_label = ""

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # ── Detect step headings ──────────────────────────────────────────
        step_match = re.match(
            r'^(#{2,5})\s+Step\s+([\d.]+(?:\.\d+)*)(?::?\s*(.*))?', stripped
        )
        if step_match:
            if current_turn and current_step:
                current_step.turns.append(current_turn)
                current_turn = None
            if current_step:
                steps.append(current_step)

            step_id = step_match.group(2)
            step_title = step_match.group(3) or ""
            step_title = step_title.strip().rstrip(":")
            current_step = Step(id=step_id, title=step_title)
            in_how_framed = False
            i += 1
            continue

        # ── Detect turn headings ──────────────────────────────────────────
        turn_match = re.match(
            r'^\*\*Turn\s+(\d+):\s*(.*?)\*\*', stripped
        )
        if turn_match and current_step:
            if current_turn:
                current_step.turns.append(current_turn)
            turn_num = turn_match.group(1)
            turn_title = turn_match.group(2).strip()
            current_turn = Turn(number=turn_num, title=turn_title, templates=[])
            in_how_framed = False
            i += 1
            continue

        # ── Detect "How this was framed:" ─────────────────────────────────
        if stripped.startswith("**How this was framed:**"):
            in_how_framed = True
            pending_variant_label = ""
            i += 1
            continue

        # ── Detect conditional variant labels ─────────────────────────────
        # Lines like: → **If AI only read questionnaire file (common case):**
        variant_match = re.match(r'^→?\s*\*\*If\s+(.*?)\*\*:?\s*$', stripped)
        if variant_match and in_how_framed:
            pending_variant_label = variant_match.group(1).strip().rstrip(":")
            i += 1
            continue

        # Also catch lines like: **previous message** or **current message**
        msg_variant = re.match(r'^\*\*(previous message|current message)\*\*\s*$', stripped)
        if msg_variant and in_how_framed:
            pending_variant_label = msg_variant.group(1)
            i += 1
            continue

        # ── Code block start ──────────────────────────────────────────────
        if stripped.startswith("```") and not in_code_block and in_how_framed:
            in_code_block = True
            code_block_lines = []
            variant_label = pending_variant_label
            pending_variant_label = ""
            i += 1
            continue

        # ── Code block end ────────────────────────────────────────────────
        if stripped.startswith("```") and in_code_block:
            in_code_block = False
            template_text = "\n".join(code_block_lines).strip()
            if template_text:
                label = variant_label if variant_label else "default"
                t = Template(label=label, text=template_text)
                if current_turn:
                    current_turn.templates.append(t)
                elif current_step:
                    current_step.standalone_templates.append(t)
            code_block_lines = []
            variant_label = ""
            i += 1
            continue

        # ── Inside code block: collect lines ──────────────────────────────
        if in_code_block:
            code_block_lines.append(line)
            i += 1
            continue

        # ── Detect validation heading → end of "how framed" zone ──────────
        if stripped.startswith("**Validation:**"):
            in_how_framed = False

        i += 1

    # flush
    if current_turn and current_step:
        current_step.turns.append(current_turn)
    if current_step:
        steps.append(current_step)

    return steps


# ── Placeholder extraction ─────────────────────────────────────────────────────

# Matches [UPPERCASE_PLACEHOLDER] — requires 2+ chars, no spaces (uses _ or . separators)
PLACEHOLDER_RE = re.compile(r'\[([A-Z][A-Z0-9_.´\']*(?:\.[A-Z0-9_.´\']*)*)\]')

# Literal markers that appear in templates but should NOT be treated as fillable placeholders
LITERAL_MARKERS = {"INSERT AREA(S) HERE", "INSERT FINAL HERE", "INSERT HERE"}


def find_placeholders(text: str) -> list:
    """Find all unique placeholder names in the template text (preserving order)."""
    seen = set()
    result = []
    for match in PLACEHOLDER_RE.finditer(text):
        name = match.group(1)
        if name not in seen and len(name) >= 2 and name not in LITERAL_MARKERS:
            seen.add(name)
            result.append(name)
    return result


# ── Memory (persistent placeholder values) ─────────────────────────────────────

def load_memory() -> dict:
    if MEMORY_FILE.exists():
        try:
            return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_memory(memory: dict):
    MEMORY_FILE.write_text(json.dumps(memory, indent=2, ensure_ascii=False), encoding="utf-8")


# ── Clipboard ──────────────────────────────────────────────────────────────────

def copy_to_clipboard(text: str):
    proc = subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)


# ── Interactive UI ─────────────────────────────────────────────────────────────

BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RED = "\033[31m"
RESET = "\033[0m"


def pick(prompt: str, options: list, display_fn=None) -> int:
    """Show numbered options, return selected index."""
    print(f"\n{BOLD}{prompt}{RESET}")
    for i, opt in enumerate(options):
        label = display_fn(opt) if display_fn else str(opt)
        print(f"  {CYAN}{i + 1}{RESET}) {label}")
    while True:
        try:
            raw = input(f"\n  Enter choice (1-{len(options)}): ").strip()
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return idx
        except (ValueError, EOFError):
            pass
        print(f"  {RED}Invalid choice.{RESET}")


SKIP_SENTINEL = object()


def prompt_for_value(placeholder: str, memory: dict, session_values: dict):
    """Prompt user for a placeholder value, offering defaults from memory.
    Returns SKIP_SENTINEL if user types !skip (placeholder left untouched).
    """
    # Check session-level values first (same run), then persistent memory
    default = session_values.get(placeholder) or memory.get(placeholder)

    hint = ""
    if "PATH" in placeholder or "DIRECTORY" in placeholder:
        hint = f" {DIM}(file/directory path){RESET}"
    elif "TEXT" in placeholder or "SECTION" in placeholder:
        hint = f" {DIM}(text block — @filepath to read from file){RESET}"
    elif "NUMBER" in placeholder or "LINES" in placeholder:
        hint = f" {DIM}(number){RESET}"
    elif "NAME" in placeholder:
        hint = f" {DIM}(name){RESET}"

    print(f"\n  {YELLOW}[{placeholder}]{RESET}{hint}")

    if default:
        # Show truncated default
        display_default = default if len(default) <= 120 else default[:117] + "..."
        print(f"  {DIM}Previous: {display_default}{RESET}")
        raw = input(f"  Value (Enter=reuse, !skip=leave as-is): ").strip()
        if raw == "":
            return default
    else:
        raw = input(f"  Value (!skip to leave as-is): ").strip()

    if raw == "!skip":
        print(f"  {DIM}Skipped — will remain as [{placeholder}]{RESET}")
        return SKIP_SENTINEL

    # If value starts with @, read file content
    if raw.startswith("@"):
        file_path = Path(raw[1:]).expanduser()
        if file_path.exists():
            content = file_path.read_text(encoding="utf-8").strip()
            print(f"  {GREEN}Read {len(content)} chars from {file_path}{RESET}")
            return content
        else:
            print(f"  {RED}File not found: {file_path} — using raw text{RESET}")

    return raw


def get_parent_id(step_id: str) -> str:
    """Get the parent step ID. e.g., '4.1.0' → '4', '6.3.1' → '6'."""
    parts = step_id.split(".")
    if len(parts) <= 1:
        return ""
    return parts[0]


def pick_step(usable_steps: list, step_titles: dict):
    """Show steps grouped under their top-level parent, return selected Step."""
    print(f"\n{BOLD}Select a step:{RESET}")

    # Group usable steps by top-level parent
    num = 0
    index_map = {}  # num → Step

    last_parent = None
    for s in usable_steps:
        parent_id = get_parent_id(s.id)

        # Show parent header if this is a sub-step and parent changed
        if parent_id and parent_id != last_parent and parent_id != s.id:
            parent_title = step_titles.get(parent_id, "")
            if parent_title:
                print(f"\n  {BOLD}Step {parent_id}: {parent_title}{RESET}")
            last_parent = parent_id

        num += 1
        index_map[num] = s

        # Indent sub-steps under their parent
        if parent_id and parent_id != s.id:
            print(f"    {CYAN}{num}{RESET}) Step {s.id}: {s.title}")
        else:
            print(f"  {CYAN}{num}{RESET}) Step {s.id}: {s.title}")

    while True:
        try:
            raw = input(f"\n  Enter choice (1-{num}): ").strip()
            idx = int(raw)
            if idx in index_map:
                return index_map[idx]
        except (ValueError, EOFError):
            pass
        print(f"  {RED}Invalid choice.{RESET}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    if not METHODOLOGY_PATH.exists():
        print(f"{RED}Methodology file not found: {METHODOLOGY_PATH}{RESET}")
        sys.exit(1)

    print(f"{BOLD}Template Filler{RESET}")
    print(f"{DIM}Parsing methodology...{RESET}")

    steps = parse_methodology(METHODOLOGY_PATH)
    if not steps:
        print(f"{RED}No steps found in the methodology file.{RESET}")
        sys.exit(1)

    memory = load_memory()
    session_values = {}  # values set during this run

    # Build a title map from ALL steps (including empty parent headers)
    step_titles = {s.id: s.title for s in steps}

    # Filter to steps that actually have templates
    usable_steps = [
        s for s in steps
        if s.turns or s.standalone_templates
    ]

    if not usable_steps:
        print(f"{RED}No steps with templates found.{RESET}")
        sys.exit(1)

    while True:
        # ── Step selection (grouped by parent) ────────────────────────────
        step = pick_step(usable_steps, step_titles)

        # Collect all available templates for this step
        all_items = []  # list of (label, Template)

        for turn in step.turns:
            if len(turn.templates) == 1:
                all_items.append((
                    f"Turn {turn.number}: {turn.title}",
                    turn.templates[0]
                ))
            else:
                for t in turn.templates:
                    all_items.append((
                        f"Turn {turn.number}: {turn.title} [{t.label}]",
                        t
                    ))

        for t in step.standalone_templates:
            all_items.append((f"(standalone) [{t.label}]", t))

        if not all_items:
            print(f"\n  {RED}No templates found for Step {step.id}.{RESET}")
            continue

        # ── Template selection ────────────────────────────────────────────
        tmpl_idx = pick(
            f"Step {step.id} — Select a template:",
            all_items,
            display_fn=lambda item: item[0]
        )
        label, template = all_items[tmpl_idx]

        # ── Show template ─────────────────────────────────────────────────
        print(f"\n{BOLD}Template:{RESET}")
        print(f"{DIM}{template.text}{RESET}")

        # ── Find and fill placeholders ────────────────────────────────────
        placeholders = find_placeholders(template.text)

        if not placeholders:
            print(f"\n  {GREEN}No placeholders found — template is ready as-is.{RESET}")
            result = template.text
        else:
            print(f"\n{BOLD}Placeholders ({len(placeholders)}):{RESET}")
            for p in placeholders:
                print(f"  - [{p}]")

            print(f"\n{BOLD}Fill each placeholder:{RESET}")
            values = {}
            for p in placeholders:
                val = prompt_for_value(p, memory, session_values)
                values[p] = val
                if val is not SKIP_SENTINEL:
                    session_values[p] = val
                    memory[p] = val

            # ── Substitute ────────────────────────────────────────────────
            result = template.text
            for p, val in values.items():
                if val is not SKIP_SENTINEL:
                    result = result.replace(f"[{p}]", val)

        # ── Verify ────────────────────────────────────────────────────────
        remaining = PLACEHOLDER_RE.findall(result)
        if remaining:
            print(f"\n  {RED}WARNING: {len(remaining)} placeholder(s) still remain:{RESET}")
            for r in remaining:
                print(f"    {RED}[{r}]{RESET}")
            proceed = input(f"\n  Copy anyway? (y/n): ").strip().lower()
            if proceed != "y":
                print("  Skipped.")
                continue
        else:
            print(f"\n  {GREEN}All placeholders filled. No remaining brackets.{RESET}")

        # ── Copy to clipboard ─────────────────────────────────────────────
        copy_to_clipboard(result)
        print(f"  {GREEN}Copied to clipboard!{RESET}")

        # ── Save memory ───────────────────────────────────────────────────
        save_memory(memory)

        # ── Continue? ─────────────────────────────────────────────────────
        again = input(f"\n  {BOLD}Fill another template? (y/n): {RESET}").strip().lower()
        if again != "y":
            break

    print(f"\n{DIM}Done.{RESET}")


if __name__ == "__main__":
    main()
