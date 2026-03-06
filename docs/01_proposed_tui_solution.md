# Proposed Solution: Template Filler TUI

**Date:** 2026-02-27
**Status:** Draft — open for refinement
**Preceded by:** [Phase 0: Situation Assessment](00_phase_0_situation_assessment_session.md)
**Current broken solution:** [template_filler.py](template_filler.py)

---

## 1. Why the Current Solution Fails

The current `template_filler.py` script addresses the right problem but fails in execution:

| Issue | Detail |
|-------|--------|
| **Still feels manual** | Sequential `input()` prompts for each placeholder — same cognitive pattern as doing it by hand |
| **Broken placeholder detection** | A single regex (`[A-Z][A-Z0-9_.]+`) designed for the old inconsistent naming conventions. The methodology placeholders have since been unified to a single `UPPER-HYPHEN-CASE` convention with a formal Placeholder Registry — the old script knows nothing about either |
| **No awareness of placeholder relationships** | Every placeholder treated independently. No concept of "these 8 placeholders share the same value across steps" |
| **Poor text-block UX** | Placeholders like `[TAILORING-METHODOLOGY-INTRO-SEC-TEXT]` or `[TAILORING-METHODOLOGY-SESSION-3-FULL-TEXT]` require pasting large content via `@filepath` hack — no preview, no browsing |
| **No workflow context** | Each template fill is an isolated event. No concept of "I'm working through Phase 3 of UX tailoring" where context carries forward |
| **No live preview** | You fill values blindly and only see the result after all placeholders are done |
| **No distinction between placeholder roles** | Fillable placeholders, insertion markers (`[INSERT AREA(S) HERE]`), and template structure tokens (`[N]`) all treated the same |

---

## 2. Proposed Solution: Terminal User Interface (TUI)

**Tech stack:** Python + [Textual](https://textual.textualize.io/)

Textual provides: split-pane layouts, tree widgets, form inputs, live-updating panels, CSS-like styling, keyboard navigation, and mouse support — all running in the terminal.

---

## 3. Fundamental Constraint: Read-Only Operation

The TUI **never modifies any file** — not the methodology file, not any source file, not any file on disk. The only things it writes are its own internal memory/config (remembered placeholder values).

Its entire job is a three-step loop:
1. **Read** a template from the methodology file
2. **Fill** placeholders interactively with user-provided values
3. **Copy** the filled result to the clipboard

Nothing else. No file creation, no file editing, no side effects beyond the clipboard and its own memory store.

---

## 4. Core UX Model

### 4.1 Session-Oriented Workflow

When the TUI launches, the user declares a **work session context**:
- **Domain** (e.g., UX, PM, Problem Definition)
- **Phase number** (e.g., Phase 0, Phase 3)
- **Directory roots** — the two file system roots used for path autocomplete on `PATH-*` placeholders:
  - `.../dev-workflow/dev-workflowWF/` — the methodology file itself (source of templates)
  - `.../dev-workflow/dev-workflow/` — all domain files: golden methodologies, split phase files, questionnaire generators, questionnaires, discovery conversations, session skeletons, phase generators, prompt generation standards, and example/reference files

This context pre-loads shared placeholder values that repeat across steps. You fill them once — they propagate everywhere.

### 4.2 Live Preview

Split-pane layout:
- **Left:** The template with placeholders highlighted (unfilled in one color, filled in another)
- **Right:** The live result — updating in real-time as each placeholder gets a value

**Handling large values in the preview:** Templates are typically ~50-70 lines of text and should remain fully visible. But some placeholders get filled with very large content (1,000+ lines — e.g., `[TAILORING-METHODOLOGY-SESSION-3-FULL-TEXT]` is the entire 25-layer methodology). Inlining those would destroy the template's visual structure.

Strategy:
- **Short values** (paths, names, numbers, text up to ~100 lines): shown inline in the preview
- **Large values** (100+ lines): shown as a **collapsed summary**, e.g., `[TAILORING-METHODOLOGY-SESSION-3-FULL-TEXT → 1,247 lines from Tailoring_Methodology...md]` — the template structure stays readable
- The user can **expand/collapse** any large value in the preview to inspect it

**Critical distinction:** Collapsing is purely a visual aid in the preview panel. The **clipboard output always contains the full expanded text** — every placeholder fully substituted, no truncation, ready to paste.

No more "did I get them all?" anxiety. You **see** the state at all times.

### 4.3 Smart Input by Placeholder Type

The unified `UPPER-HYPHEN-CASE` naming convention makes UI type **deterministic from the placeholder name** — no heuristics needed:

| Name pattern | UI type | Input method | Count |
|-------------|---------|--------------|-------|
| `PATH-*` | PATH | Inline text input with `@` prepend (display/output only) | 25 |
| `*-TEXT` | TEXT | Multi-line TextArea | 8 |
| `*-NAME` / `PATH-COMPONENT-*` | NAME | Inline text input | 5 |
| `*-LIST` | LIST | Multi-line TextArea | 2 |
| `*-DIR` | NAME | Inline text input (directory path without `@`) | — |
| `AI-*` | AI-FEEDBACK | Multi-line TextArea | 3 |
| `[INSERT ...]`, `[N]`, `[Domain-Specific Name]`, `[domain]`, `[DOMAIN]` | STRUCTURAL | **Not shown as fillable** — visually distinct, skipped automatically | 6 |

Rules are checked top to bottom, first match wins. If `PATH-*` and `*-DIR` both match (e.g., `PATH-SOMETHING-DIR`), `PATH-*` wins. Fallback for unmatched names: NAME (inline text input).

Total: **43 fillable** + **6 structural** (not fillable) = 49 placeholder tokens in code blocks.

Source of truth: `Placeholder_Registry.md` (maintained alongside the methodology file).

### 4.4 Workflow Navigation

A **sidebar** showing the step tree:
```
Step 1: Golden Methodology Prompt Generator
Step 2: Golden Methodology Generation
Step 3: Golden Methodology Segmentation
  Step 3.1: Understand the Splitting Pattern
    Step 3.1.1: Clarify the Request
    Step 3.1.2: Approve and Execute Analysis
  Step 3.2: Propose and Execute Segmentation
    ...
Step 4: Create Discovery Workflow Generators
  ...
```

- Steps with templates appear selectable
- Filled steps get a checkmark
- Context (placeholder values) carries forward from step to step

---

## 5. Placeholder Handling Strategy

### 5.1 Detection

A placeholder is any `[...]` token inside a code-block template. All 43 registered placeholders use a single unified `UPPER-HYPHEN-CASE` convention, so detection is straightforward:

- Match `[UPPER-HYPHEN-CASE-TOKEN]` patterns in template text
- Cross-reference against the Placeholder Registry for known fillable placeholders
- Any `[...]` token NOT in the registry is treated as structural (not fillable)

The 6 structural tokens (`[INSERT AREA(S) HERE]`, `[INSERT FINAL HERE]`, `[N]`, `[Domain-Specific Name]`, `[domain]`, `[DOMAIN]`) are recognized and skipped — they are not in the registry and are never prompted for input.

### 5.2 UI Type Derivation

The placeholder naming convention encodes the UI type deterministically:

| Name pattern | UI type | Derivation rule |
|-------------|---------|----------------|
| Starts with `PATH-` | PATH | Path input with autocomplete |
| Ends with `-TEXT` | TEXT | File picker with preview |
| Ends with `-NAME` or starts with `PATH-COMPONENT-` | NAME | Inline text input |
| Ends with `-LIST` | LIST | Multi-line input |
| Starts with `AI-` | AI-FEEDBACK | Multi-line paste input |

No ambiguity — every registered placeholder matches exactly one rule.

### 5.3 Placeholder Values

Placeholder values are managed through two mechanisms:

#### Registry Values (Persistent)

The Placeholder Registry (`Placeholder_Registry.md`) has a **Value** column. When the TUI launches, it reads this column and pre-fills any placeholder that has a value defined.

The Value column follows these conventions:

| Value column content | TUI behavior |
|---|---|
| Empty | Ask the user to fill it manually |
| Direct value (e.g., `/Users/.../file.md`) | Pre-fill the input with this value; user must confirm to use it |
| File reference (`@/path/to/file.md`) | Read the entire file's content, pre-fill the input with that content; user must confirm |
| File reference with extractor (`@/path/to/file.md::extractor(args)`) | Read the file and extract only the matched portion; user must confirm |

**Extraction syntax:** File references can include `::` followed by an extractor to load only a specific portion of a file:

- `between(START, END)` — text between the first occurrence of `START` and the next `END` (markers excluded)
- `heading(## Section Name)` — markdown section under the specified heading, up to the next same-or-higher-level heading
- `lines(start, end)` — line range by number (1-indexed, inclusive)

No extractor means the entire file is loaded (backwards compatible). First match wins when a pattern appears multiple times. Missing matches fail hard — same as missing file references.

This is the single source of truth for persistent/global values. To add, change, or remove a persistent value, the user edits the registry file directly — the same way they edit the methodology file to change templates.

#### PATH-type `@` Prefix

For PATH-type placeholders (names starting with `PATH-`), the `@` prefix is strictly a **display and output concern** — it is never part of the stored value.

- **Stored values** (registry Value column, session memory): always clean paths without `@` (e.g., `/Users/.../file.md`)
- **Input field**: `@` is prepended for display (e.g., `@/Users/.../file.md`)
- **Live preview**: `@` is prepended at render time
- **Clipboard output**: `@` is prepended at copy time

When a PATH value is confirmed, the `@` is stripped before storing. This ensures session memory values always match the registry format, and the `@` is only added at the moment it's needed for display or output.

**Important:** The `@` prefix in the registry Value column (for file references) and the `@` prefix for PATH-type outputs are two different things:
- Registry `@/path` → "read this file's content" (used for large TEXT-type values)
- PATH-type output `@/path` → literal prefix that appears in the final template output

#### Runtime Extraction (Exception)

File reading is exclusively a registry load-time operation, with one exception: if the user types `@/path/to/file::extractor(args)` into any input field at runtime and confirms, the TUI reads the file, applies the extractor, and replaces the placeholder with the extracted content — not the path.

This only triggers when `::` is present. A plain `@/path` entered at runtime is never read as a file — it remains a literal value. The same three extractors available in the registry (`between`, `heading`, `lines`) work at runtime with the same rules (first match wins, stripped, missing match shows an error).

#### Session Values (Temporary)

Values entered during a session are remembered for the duration of that session. If the same placeholder appears in multiple templates within a session, the previously entered value is offered as the default. Session values are stored in the same format as the registry — clean values without display prefixes. Session values are not persisted — they are lost when the app closes.

---

## 6. Key Screens / Views

### 6.1 Session Setup Screen
- Select or create a work session (domain, phase, directory roots)
- Shows previously saved sessions for quick resume

### 6.2 Step Browser Screen
- Sidebar: step tree with hierarchy (Steps 1-8, sub-steps, turns)
- Main area: selected step's description and available templates
- Visual indicators: filled (checkmark), partially filled, unfilled

### 6.3 Template Fill Screen
- **Top bar:** Step name, template variant label
- **Left panel:** Template source with placeholder highlighting
  - Unfilled placeholders: highlighted in yellow/orange
  - Filled placeholders: highlighted in green (showing the substituted value, truncated)
  - Insertion markers / structure tokens: dimmed, visually distinct
- **Right panel:** Live preview of the filled result
- **Bottom panel:** Placeholder input area
  - Shows current placeholder name and description
  - Type-appropriate input widget (path autocomplete, file picker, text input, multi-line)
  - Pre-filled from registry values or session memory; user must confirm to accept
  - **Content Preview button** — positioned next to the placeholder name, opens a scrollable read-only modal overlay showing the full content of the current input. Available only when the input has content (pre-filled or typed/pasted). Dismissed with Esc or [X] button. Also accessible via Ctrl+O. The preview header shows:
    - **Line count** — always displayed (e.g., "248 lines")
    - **Source file path** (full, wraps to multiple lines if needed) — only displayed when the value was loaded from a file via `@` reference in the registry. Not shown for values that were typed/pasted or stored as literal text in the registry.
- **Footer:** Keyboard shortcuts

### 6.5 Keyboard Shortcuts (Template Fill Screen)

| Shortcut | Action |
|---|---|
| Tab | Next placeholder |
| Enter | Confirm value (in Input widget) |
| Ctrl+O | Open content preview |
| Ctrl+Y | Copy filled template to clipboard |
| Esc | Go back to step browser |

### 6.4 Output / Copy Screen
- Full preview of the final filled template
- Remaining unfilled placeholders highlighted (if any)
- One keypress to copy to clipboard
- Option to move to next step in sequence

---

## 7. Architecture Overview

```
template_filler_tui/
    __init__.py
    app.py              # Textual App entry point
    screens/
        session_setup.py
        step_browser.py
        template_fill.py
    models/
        methodology.py   # Parsing: markdown -> Steps/Turns/Templates
        placeholder.py   # Registry lookup, name-pattern UI type derivation, substitution
        memory.py        # Session/domain/global value storage
    widgets/
        step_tree.py     # Sidebar tree widget
        template_view.py # Highlighted template display
        preview.py       # Live preview panel
        input_area.py    # Smart input by placeholder type
    config.py            # Paths, known directory roots, settings
    data/
        memory.json      # Persistent placeholder values
```

### 7.1 Parsing Pipeline

```
Methodology .md file
    -> parse into Steps (id, title)
        -> each Step has Turns (number, title)
            -> each Turn has Templates (label, raw text)
        -> or standalone Templates
    -> for each Template:
        -> detect all [...] tokens
        -> look up each token in the Placeholder Registry
        -> in registry = fillable (UI type derived from name pattern)
        -> not in registry = structural, skip automatically
        -> extract fillable placeholders in order of appearance
```

### 7.2 Data Flow

```
User selects Step + Template
    -> Template text + placeholder list displayed
    -> For each fillable placeholder:
        -> Check registry Value column, then session memory
        -> If found: pre-fill input, user confirms or overrides
        -> If not found: prompt with type-appropriate input
        -> On fill: update live preview immediately
    -> All filled -> copy to clipboard
    -> Save values to memory
    -> Advance to next step
```

---

## 8. Open Questions for Refinement

- [x] ~~Should the TUI support editing the methodology file itself, or is it strictly read-only?~~ **Answered: Strictly read-only. Never modify any file. Read, fill, copy to clipboard.**
- [x] ~~How should conditional template variants be presented?~~ **Answered: When a turn has multiple variants (e.g., "If AI only read questionnaire", "If AI already read both files"), show them as a selectable list — user picks the one that matches their situation.**
- [x] ~~Should the TUI track which steps have been completed for a given domain/phase engagement?~~ **Answered: Yes. The session tracks which steps have been filled. When resuming a saved session, completed steps are visually marked and the user can pick up where they left off.**

---

**Next step:** Refine this proposal based on feedback, then begin development.
