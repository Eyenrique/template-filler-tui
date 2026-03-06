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
    value: str | None = None  # pre-filled value from registry Value column
    source_path: str | None = None  # file path if value was loaded via @ reference


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
    if name.endswith("-DIR"):
        return UIType.NAME
    return UIType.NAME  # fallback for registered but unmatched


def load_registry(path: Path) -> dict[str, PlaceholderInfo]:
    """Load the Placeholder Registry markdown and return a dict of name -> PlaceholderInfo."""
    text = path.read_text(encoding="utf-8")
    registry: dict[str, PlaceholderInfo] = {}

    # Parse the markdown table rows
    # Format: | `[PLACEHOLDER-NAME]` | Description | Value |
    row_re = re.compile(
        r'^\|\s*`\[([^\]]+)\]`\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|$'
    )

    for line in text.split("\n"):
        m = row_re.match(line.strip())
        if m:
            name = m.group(1)
            description = m.group(2).strip()
            raw_value = m.group(3).strip()
            ui_type = derive_ui_type(name)

            # Resolve the value
            value, source_path = _resolve_value(raw_value) if raw_value else (None, None)

            registry[name] = PlaceholderInfo(
                name=name,
                description=description,
                ui_type=ui_type,
                value=value,
                source_path=source_path,
            )

    return registry


def _resolve_value(raw: str) -> tuple[str | None, str | None]:
    """Resolve a registry Value column entry.

    Returns (value, source_path) where:
    - Empty or whitespace -> (None, None)
    - Starts with @ -> (file content, file path)
    - @/path::extractor(args) -> (extracted portion, file path)
    - Otherwise -> (literal value, None)
    """
    raw = raw.strip()
    if not raw:
        return None, None

    # Strip surrounding backticks if present (markdown formatting)
    if raw.startswith("`") and raw.endswith("`"):
        raw = raw[1:-1].strip()

    if raw.startswith("@"):
        ref = raw[1:]

        # Split file path from extractor at ::
        extractor = None
        if "::" in ref:
            path_part, extractor = ref.split("::", 1)
        else:
            path_part = ref

        file_path = Path(path_part.strip()).expanduser()
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(
                f"Registry file reference not found: {file_path}"
            )
        content = file_path.read_text(encoding="utf-8")

        if extractor:
            content = _apply_extractor(content, extractor.strip(), str(file_path))
        else:
            content = content.strip()

        return content, str(file_path)

    return raw, None


# Matches extractor calls like: between(X, Y), heading(## Foo), lines(1, 20)
_EXTRACTOR_RE = re.compile(r'^(\w+)\((.+)\)$', re.DOTALL)


def _apply_extractor(content: str, extractor: str, file_path: str) -> str:
    """Apply an extraction rule to file content."""
    m = _EXTRACTOR_RE.match(extractor)
    if not m:
        raise ValueError(f"Invalid extractor syntax: {extractor}")

    name = m.group(1)
    args_str = m.group(2)

    if name == "between":
        return _extract_between(content, args_str, file_path)
    elif name == "heading":
        return _extract_heading(content, args_str, file_path)
    elif name == "lines":
        return _extract_lines(content, args_str, file_path)
    else:
        raise ValueError(f"Unknown extractor: {name}")


def _extract_between(content: str, args_str: str, file_path: str) -> str:
    """Extract text between first occurrence of START and next END (markers excluded)."""
    # Split on first comma that's not inside the markers themselves
    parts = args_str.split(",", 1)
    if len(parts) != 2:
        raise ValueError(f"between() requires two arguments, got: {args_str}")

    start_marker = parts[0].strip()
    end_marker = parts[1].strip()

    start_idx = content.find(start_marker)
    if start_idx == -1:
        raise ValueError(
            f"Extractor between(): start marker {start_marker!r} not found in {file_path}"
        )

    after_start = start_idx + len(start_marker)
    end_idx = content.find(end_marker, after_start)
    if end_idx == -1:
        raise ValueError(
            f"Extractor between(): end marker {end_marker!r} not found after start marker in {file_path}"
        )

    return content[after_start:end_idx].strip()


def _extract_heading(content: str, args_str: str, file_path: str) -> str:
    """Extract markdown section under a heading, up to next same-or-higher-level heading."""
    heading = args_str.strip()

    # Determine heading level from the # prefix
    level = 0
    for ch in heading:
        if ch == "#":
            level += 1
        else:
            break

    if level == 0:
        raise ValueError(f"heading() argument must start with #: {heading}")

    lines = content.split("\n")
    start_line = None

    for i, line in enumerate(lines):
        if line.strip() == heading:
            start_line = i + 1
            break

    if start_line is None:
        raise ValueError(
            f"Extractor heading(): heading {heading!r} not found in {file_path}"
        )

    # Collect lines until next same-or-higher-level heading
    result_lines = []
    heading_re = re.compile(r'^(#{1,' + str(level) + r'})\s')

    for i in range(start_line, len(lines)):
        if heading_re.match(lines[i]):
            break
        result_lines.append(lines[i])

    return "\n".join(result_lines).strip()


def _extract_lines(content: str, args_str: str, file_path: str) -> str:
    """Extract a range of lines (1-indexed, inclusive)."""
    parts = args_str.split(",", 1)
    if len(parts) != 2:
        raise ValueError(f"lines() requires two arguments, got: {args_str}")

    try:
        start = int(parts[0].strip())
        end = int(parts[1].strip())
    except ValueError:
        raise ValueError(f"lines() arguments must be integers, got: {args_str}")

    lines = content.split("\n")
    if start < 1 or end < start or start > len(lines):
        raise ValueError(
            f"Extractor lines({start}, {end}): out of range for {file_path} ({len(lines)} lines)"
        )

    # Clamp end to file length
    end = min(end, len(lines))
    return "\n".join(lines[start - 1:end]).strip()


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


# Matches UPPER-HYPHEN-CASE names (real placeholder convention)
_PLACEHOLDER_NAME_RE = re.compile(r'^[A-Z][A-Z0-9]+(-[A-Z0-9]+)+$')


def find_unregistered_placeholders(
    steps: list,
    registry: dict[str, "PlaceholderInfo"],
) -> list[str]:
    """Find tokens in methodology templates that look like placeholders
    (UPPER-HYPHEN-CASE) but are not in the registry.

    These are likely placeholders that were renamed in the methodology
    but not updated in the registry.
    """
    unregistered: set[str] = set()

    for step in steps:
        for turn in step.turns:
            for tmpl in turn.templates:
                tokens = find_tokens(tmpl.text)
                _, structural = classify_tokens(tokens, registry)
                for token in structural:
                    if _PLACEHOLDER_NAME_RE.match(token):
                        unregistered.add(token)
        for tmpl in step.standalone_templates:
            tokens = find_tokens(tmpl.text)
            _, structural = classify_tokens(tokens, registry)
            for token in structural:
                if _PLACEHOLDER_NAME_RE.match(token):
                    unregistered.add(token)

    return sorted(unregistered)


def substitute(template_text: str, values: dict[str, str]) -> str:
    """Replace all [PLACEHOLDER] tokens with their values."""
    result = template_text
    for name, value in values.items():
        result = result.replace(f"[{name}]", value)
    return result
