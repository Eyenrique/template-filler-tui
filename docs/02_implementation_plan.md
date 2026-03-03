# Implementation Plan: Template Filler TUI

**Date:** 2026-03-01
**Status:** Draft
**Based on:** [Proposed TUI Solution](01_proposed_tui_solution.md)

---

## Phase 1: Project Setup

- Initialize Python project structure (`template_filler_tui/` package)
- Add `pyproject.toml` with Textual dependency
- Create entry point (`__main__.py` or CLI script)

## Phase 2: Core Logic (no UI)

Build and verify the foundation before touching any TUI code.

### 2.1 Methodology Parser (`models/methodology.py`)

- Parse `Tailoring_Methodology_state_capture.md` into Steps → Turns → Templates
- Extract code-block templates from "How this was framed:" sections
- Handle conditional variants (multiple templates per turn)
- Output: list of Step objects with their template hierarchy

### 2.2 Placeholder System (`models/placeholder.py`)

- Load `Placeholder_Registry.md` as the source of truth, including the **Value** column
- Detect `[...]` tokens in template text
- Registry lookup: in registry → fillable, not in registry → structural (skip)
- UI type derivation from name pattern (first match wins): `PATH-COMPONENT-*` → NAME, `PATH-*` → PATH, `AI-*` → AI-FEEDBACK, `*-TEXT` → TEXT, `*-NAME` → NAME, `*-LIST` → LIST, `*-DIR` → NAME, fallback → NAME
- Registry value loading:
  - Empty Value column → no pre-fill, ask the user
  - Direct value → store as the pre-fill value
  - `@/path/to/file` → read file content, store as the pre-fill value
- PATH-type `@` prefix handling — `@` is strictly a display/output concern, never stored:
  - On confirm: strip `@` before storing in session memory and values
  - On display (input field, live preview, clipboard): prepend `@` at render/output time
  - Stored values always match registry format (clean paths without `@`)
- Substitution: replace fillable placeholders with provided values

### 2.3 Session Memory (`models/memory.py`)

- Single layer: session values (temporary, not persisted)
- Values entered during a session are remembered for the duration of that session
- If the same placeholder appears in multiple templates, the previously entered value is offered as the default
- Session values are stored in the same format as registry values — clean, no display prefixes
- Registry values (from the Value column) serve as the persistent/global layer — managed by editing the registry file directly, not through the TUI

### 2.4 Verification

- Run parser against the real methodology file — confirm all steps, turns, and templates are extracted correctly
- Run placeholder detection against each extracted template — confirm all 43 registered placeholders are found and typed correctly
- Confirm structural tokens are identified and skipped

## Phase 3: TUI Screens

### 3.1 App Shell (`app.py`)

- Textual App with screen navigation
- Global keyboard shortcuts (Esc: back, Ctrl+C: quit)

### 3.2 Session Setup Screen (`screens/session_setup.py`)

- Domain input
- Phase number input
- Directory roots (pre-filled with known defaults, editable)
- List of previously saved sessions for quick resume

### 3.3 Step Browser Screen (`screens/step_browser.py`)

- Sidebar: step tree widget showing hierarchy (Steps 1–8, sub-steps, turns)
- Main area: selected step description and available templates
- Conditional variant selection when a turn has multiple templates
- Visual indicators: completed (checkmark), unfilled

### 3.4 Template Fill Screen (`screens/template_fill.py`)

- **Left panel:** Template source with placeholder highlighting (unfilled: yellow/orange, filled: green, structural: dimmed)
- **Right panel:** Live preview — updates in real-time as values are filled
- **Collapsed large values** in preview (100+ lines shown as summary, expandable)
- **Bottom panel:** Placeholder input area with type-appropriate widget:
  - PATH → path input with autocomplete from directory roots
  - TEXT → file picker with preview
  - NAME → inline text input
  - LIST → multi-line input
  - AI-FEEDBACK → multi-line paste
- Pre-fill: registry values and session values shown in input, user confirms or overrides
- **Content Preview**: a "Preview" button next to the placeholder name + Ctrl+O shortcut
  - Opens a scrollable, read-only modal overlay showing the full content of the current input
  - Available only when the input has content (pre-filled or typed/pasted)
  - Dismissed with Esc or [X] button
  - Strictly read-only — no editing from the preview
  - Header displays line count (always) and source file path as full path, wrapping to multiple lines if needed (only for values loaded via `@` file reference in registry)
- **Keyboard shortcuts:** Tab (next placeholder), Enter (confirm value), Ctrl+O (content preview), Ctrl+Y (copy to clipboard), Esc (back)
- Copy to clipboard on completion

## Phase 4: Integration and Polish

- Wire all screens together with session context flowing through
- Registry values loaded on launch, pre-filling placeholders across all templates
- Clipboard output: always full expanded text (no collapse)
- Edge cases: templates with zero fillable placeholders (ready as-is), empty templates

## Build Order

```
Phase 1 → Phase 2.1 → Phase 2.2 → Phase 2.3 → Phase 2.4
    → Phase 3.1 → Phase 3.2 → Phase 3.3 → Phase 3.4
    → Phase 4
```

Each phase is testable independently. Phase 2 can be verified against the real methodology file before any UI exists.

---

**Next step:** Begin Phase 1.
