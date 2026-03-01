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
| `PATH-*` | PATH | Path input with **autocomplete** from the known directory roots | 25 |
| `*-TEXT` | TEXT | File picker → reads content → shows preview before confirming | 8 |
| `*-NAME` / `PATH-COMPONENT-*` | NAME | Inline text input with session memory | 5 |
| `*-LIST` | LIST | Multi-line input or file picker | 2 |
| `AI-*` | AI-FEEDBACK | Multi-line paste input | 3 |
| `[INSERT ...]`, `[N]`, `[Domain-Specific Name]`, `[domain]`, `[DOMAIN]` | STRUCTURAL | **Not shown as fillable** — visually distinct, skipped automatically | 6 |

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

### 5.3 Memory Layers

Three layers of value memory, checked in order:

| Layer | Scope | Persists | Example |
|-------|-------|----------|---------|
| **Session values** | Changes per session | Until session ends | `[PATH-DISC-CONV-NEXT-PHASE-FILE]` — different each time |
| **Domain values** | Changes per domain | Across sessions | `[PATH-GOLDEN-METHODOLOGY-NEXT-PHASE-FILE]` — different for UX vs PM |
| **Global values** | Never changes | Across sessions | `[PATH-PROMPT-GENERATION-STANDARDS-FILE]`, `[PATH-EXAMPLE-DISC-CONV-UX-PHASE-0-FILE]` — same always |

When a placeholder is encountered:
1. Check session values first
2. Then domain values
3. Then global values
4. If no match — prompt the user

The user can override any remembered value at any time.

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
  - Shows current placeholder being filled
  - Type-appropriate input widget (path autocomplete, file picker, text input, multi-line)
  - Shows remembered value if available (press Enter to reuse)
- **Footer:** Keyboard shortcuts (Tab: next placeholder, Enter: confirm, Ctrl+C: copy result, Esc: back)

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
        -> Check memory layers (session -> domain -> global)
        -> If found: show remembered value, user confirms or overrides
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
