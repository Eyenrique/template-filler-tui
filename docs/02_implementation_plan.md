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

- Load `Placeholder_Registry.md` as the source of truth
- Detect `[...]` tokens in template text
- Registry lookup: in registry → fillable, not in registry → structural (skip)
- UI type derivation from name pattern: `PATH-*` → PATH, `*-TEXT` → TEXT, `*-NAME` → NAME, `*-LIST` → LIST, `AI-*` → AI-FEEDBACK
- Substitution: replace fillable placeholders with provided values

### 2.3 Memory System (`models/memory.py`)

- Three layers: session, domain, global
- Persistence: save/load from JSON file
- Lookup order: session → domain → global
- Override support: user can change any remembered value

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
- Memory pre-fill: show remembered value, Enter to reuse
- **Footer:** keyboard shortcuts
- Copy to clipboard on completion

## Phase 4: Integration and Polish

- Wire all screens together with session context flowing through
- Session persistence: track completed steps per domain/phase
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
