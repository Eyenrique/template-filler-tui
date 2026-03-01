"""Placeholder detection, registry lookup, UI type derivation, and substitution."""

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class UIType(Enum):
    """UI input type derived from placeholder name pattern."""
    PATH = "path"              # PATH-* prefix → path input with autocomplete
    TEXT = "text"              # *-TEXT suffix → file picker with preview
    NAME = "name"              # *-NAME suffix or PATH-COMPONENT-* → inline text input
    LIST = "list"              # *-LIST suffix → multi-line input
    AI_FEEDBACK = "ai_feedback"  # AI-* prefix → multi-line paste
    STRUCTURAL = "structural"  # not in registry → not fillable


@dataclass
class PlaceholderInfo:
    """A registered placeholder with its metadata."""
    name: str           # e.g., "PATH-EXAMPLE-GOLDEN-METHODOLOGY-FILE-UX"
    description: str    # from the registry
    ui_type: UIType     # derived from name pattern


# Matches any [...] token in template text
TOKEN_RE = re.compile(r'\[([^\[\]]+)\]')


def derive_ui_type(name: str) -> UIType:
    """Derive the UI input type from a placeholder name pattern."""
    if name.startswith("PATH-COMPONENT-"):
        return UIType.NAME
    if name.startswith("PATH-"):
        return UIType.PATH
    if name.startswith("AI-"):
        return UIType.AI_FEEDBACK
    if name.endswith("-TEXT"):
        return UIType.TEXT
    if name.endswith("-NAME"):
        return UIType.NAME
    if name.endswith("-LIST"):
        return UIType.LIST
    return UIType.PATH  # fallback for registered but unmatched


def load_registry(path: Path) -> dict[str, PlaceholderInfo]:
    """Load the Placeholder Registry markdown and return a dict of name -> PlaceholderInfo."""
    text = path.read_text(encoding="utf-8")
    registry: dict[str, PlaceholderInfo] = {}

    # Parse the markdown table rows
    # Format: | Line(s) | `[PLACEHOLDER-NAME]` | Description |
    row_re = re.compile(
        r'^\|\s*[\d,\s]+\s*\|\s*`\[([^\]]+)\]`\s*\|\s*(.*?)\s*\|$'
    )

    for line in text.split("\n"):
        m = row_re.match(line.strip())
        if m:
            name = m.group(1)
            description = m.group(2).strip()
            ui_type = derive_ui_type(name)
            registry[name] = PlaceholderInfo(
                name=name,
                description=description,
                ui_type=ui_type,
            )

    return registry


def find_tokens(template_text: str) -> list[str]:
    """Find all [...] tokens in template text, preserving order, deduped."""
    seen: set[str] = set()
    result: list[str] = []
    for m in TOKEN_RE.finditer(template_text):
        name = m.group(1)
        if name not in seen:
            seen.add(name)
            result.append(name)
    return result


def classify_tokens(
    tokens: list[str],
    registry: dict[str, PlaceholderInfo],
) -> tuple[list[PlaceholderInfo], list[str]]:
    """Classify tokens into fillable (in registry) and structural (not in registry).

    Returns (fillable, structural) where fillable is a list of PlaceholderInfo
    and structural is a list of token names.
    """
    fillable: list[PlaceholderInfo] = []
    structural: list[str] = []

    for token in tokens:
        if token in registry:
            fillable.append(registry[token])
        else:
            structural.append(token)

    return fillable, structural


def substitute(template_text: str, values: dict[str, str]) -> str:
    """Replace all [PLACEHOLDER] tokens with their values."""
    result = template_text
    for name, value in values.items():
        result = result.replace(f"[{name}]", value)
    return result
