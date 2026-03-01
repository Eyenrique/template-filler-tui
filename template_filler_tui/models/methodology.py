"""Parse the Tailoring Methodology markdown into Steps, Turns, and Templates."""

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Template:
    """A single code-block template from the methodology."""
    label: str       # e.g., "If AI only read questionnaire file (common case)"
    text: str        # the raw template text inside the code block


@dataclass
class Turn:
    """A turn within a step (Turn 1, Turn 2, …)."""
    number: str      # e.g., "1", "2"
    title: str       # e.g., "Initial Understanding"
    templates: list[Template] = field(default_factory=list)


@dataclass
class Step:
    """A step (or sub-step) in the methodology."""
    id: str          # e.g., "3.1.1", "6.1", "8"
    title: str       # e.g., "Golden Methodology Prompt Generator"
    turns: list[Turn] = field(default_factory=list)
    standalone_templates: list[Template] = field(default_factory=list)

    @property
    def has_templates(self) -> bool:
        if self.standalone_templates:
            return True
        return any(t.templates for t in self.turns)

    @property
    def parent_id(self) -> str:
        parts = self.id.split(".")
        if len(parts) <= 1:
            return ""
        return parts[0]


def parse_methodology(path: Path) -> list[Step]:
    """Parse the methodology markdown into a list of Step objects."""
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")

    steps: list[Step] = []
    current_step: Step | None = None
    current_turn: Turn | None = None
    in_how_framed = False
    in_code_block = False
    code_block_lines: list[str] = []
    variant_label = ""
    pending_variant_label = ""

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # ── Detect step headings ──
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
            step_title = (step_match.group(3) or "").strip().rstrip(":")
            current_step = Step(id=step_id, title=step_title)
            in_how_framed = False
            i += 1
            continue

        # ── Detect turn headings ──
        turn_match = re.match(
            r'^\*\*Turn\s+(\d+):\s*(.*?)\*\*', stripped
        )
        if turn_match and current_step:
            if current_turn:
                current_step.turns.append(current_turn)
            turn_num = turn_match.group(1)
            turn_title = turn_match.group(2).strip()
            current_turn = Turn(number=turn_num, title=turn_title)
            in_how_framed = False
            i += 1
            continue

        # ── Detect "How this was framed:" ──
        if stripped.startswith("**How this was framed:**"):
            in_how_framed = True
            pending_variant_label = ""
            i += 1
            continue

        # ── Detect conditional variant labels ──
        variant_match = re.match(r'^→?\s*\*\*If\s+(.*?)\*\*:?\s*$', stripped)
        if variant_match and in_how_framed:
            pending_variant_label = variant_match.group(1).strip().rstrip(":")
            i += 1
            continue

        # Also catch lines like: **previous message** or **current message**
        msg_variant = re.match(
            r'^\*\*(previous message|current message)\*\*\s*$', stripped
        )
        if msg_variant and in_how_framed:
            pending_variant_label = msg_variant.group(1)
            i += 1
            continue

        # ── Code block start ──
        if stripped.startswith("```") and not in_code_block and in_how_framed:
            in_code_block = True
            code_block_lines = []
            variant_label = pending_variant_label
            pending_variant_label = ""
            i += 1
            continue

        # ── Code block end ──
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

        # ── Inside code block: collect lines ──
        if in_code_block:
            code_block_lines.append(line)
            i += 1
            continue

        # ── Detect validation heading → end of "how framed" zone ──
        if stripped.startswith("**Validation:**"):
            in_how_framed = False

        i += 1

    # flush
    if current_turn and current_step:
        current_step.turns.append(current_turn)
    if current_step:
        steps.append(current_step)

    return steps
