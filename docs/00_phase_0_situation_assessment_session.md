# Problem Recognition and Situation Assessment Discovery Session
**Date:** 2026-02-26
**Status:** Completed
**Engagement Name:** [Pending - not yet captured]

## Area 1: Engagement and Situation Context
- **Situation type:** Operational/process problem — a multi-step document creation workflow with manual copy-paste and placeholder substitution
- **Urgency level:** Important (meaningful impact, not crisis — slowing down a productive workflow)
- **Situation description (team's words):** "I have a documented process to create some 'files' but this process involves copy and paste some namely text templates and I need to substitute some namely 'placeholders' into these text templates. This manually copy and paste (I select manually the text) and the placeholder substitution is slowing down the process — I'd like to make it faster."
- **Worst part identified:** Placeholder substitution — specifically, ensuring every placeholder gets the right value. "The worse part is to make sure that I replaced the placeholders with the right text — this is the part that slows down more the process because this needs to be correct."
- **Who initiated:** Self-initiated
- **Scale:** Individual practitioner
- **Process documented:** Yes — the Tailoring Methodology (8-step process for transforming comprehensive methodologies into tailored implementations)
- **Data environment:** Moderate — documented process exists, template files exist on disk, placeholders are named/identifiable in the text
- **Organization size:** Solo practitioner / freelancer

## Area 2: Triggering Signal Capture
- **Core problem confirmed:** Placeholder substitution is the bottleneck — specifically ensuring every placeholder gets the right value without missing any or mixing them up
- **Placeholder definition:** A placeholder is any text enclosed in square brackets `[...]` that appears inside a code-block template (delimited by triple backticks) and is meant to be replaced with a concrete value before use.
- **Placeholder registry:** All placeholders are cataloged in `Placeholder_Registry.md` (maintained alongside the methodology file)
- **Total unique registered placeholders: 43** (fillable, user-provided values) + **6 structural tokens** (not fillable) across 49 code blocks in the methodology
- **Naming convention: single, unified `UPPER-HYPHEN-CASE`** — all 43 registered placeholders follow one consistent convention (e.g., `[PATH-EXAMPLE-GOLDEN-METHODOLOGY-FILE-UX]`, `[TAILORING-METHODOLOGY-INTRO-SEC-TEXT]`, `[DISC-CONV-NEXT-PHASE-FILE-NAME]`)
- **Placeholder semantic categories (what they represent):**

| Category | Description | Examples | Count |
|----------|-------------|----------|-------|
| PATH — File/directory paths | Full paths or directory paths to files on disk | `[PATH-SPLIT-GOLDEN-METHODOLOGY-NEXT-PHASE-FILE]`, `[PATH-DISC-CONV-NEXT-PHASE-OUTPUT-DIR]` | 25 unique |
| TEXT — Text blocks | Large content to paste — methodology sections, prompt text, questionnaire portions | `[TAILORING-METHODOLOGY-INTRO-SEC-TEXT]`, `[DISC-WFQ-GEN-NEXT-PHASE-PROMPT-TEXT]` | 8 unique |
| NAME — Names/identifiers | File names (not full paths), directory name components | `[EXAMPLE-DISC-CONV-UX-PHASE-0-FILE-NAME]`, `[PATH-COMPONENT-DISC-WFQ-GEN-NEXT-PHASE-DIR]` | 5 unique |
| LIST — Lists/compound references | Multi-file listings, pairing examples | `[EXAMPLE-DISC-WFQ-GEN+SPLIT-GOLDEN-METHODOLOGY-PHASE-FILE-PAIRING-LIST]`, `[EXAMPLE-DISC-WFQ-UX-FILE-LIST]` | 2 unique |
| AI-FEEDBACK — AI response excerpts | Quotes from AI responses used in correction/feedback turns | `[AI-RESPONSE-ACCURATE-PART-TEXT]`, `[AI-UNREQUESTED-OUTPUT-TEXT]` | 3 unique |
| STRUCTURAL — Not fillable | Insertion markers and template structure tokens — skipped automatically | `[INSERT AREA(S) HERE]`, `[INSERT FINAL HERE]`, `[N]`, `[Domain-Specific Name]`, `[domain]`, `[DOMAIN]` | 6 tokens |

- **UI type is derivable from the placeholder name** — `PATH-*` prefixed placeholders are paths, `*-TEXT` suffixed are text blocks, `*-NAME` suffixed are names, `*-LIST` suffixed are lists. No heuristics needed.
- **Most frequently repeated placeholder:** `[EXAMPLE-DISC-CONV-UX-PHASE-0-FILE-NAME]` — 12 occurrences across code blocks
- **Typical placeholders per step template:** 3–8 unique placeholders (heaviest steps reach 7–8)
- **Frequently repeated placeholders:** Some paths and names repeat across many steps with the same value — e.g., `[PATH-EXAMPLE-DISC-CONV-UX-PHASE-0-FILE]` (10 occurrences), `[EXAMPLE-DISC-WFQ-UX-PHASE-0-FILE-NAME]` (8 occurrences)
- **Variable placeholders:** Others change each time depending on the domain/phase being worked on (e.g., `[PATH-DISC-CONV-NEXT-PHASE-FILE]`, `[DISC-CONV-NEXT-PHASE-FILE-NAME]`)
- **Current lookup method:** User already knows values in their head; browses file system for paths; opens files to copy text blocks
- **Core pain (team's own words):** "The verification anxiety — did I get them all, did I get them right, did I skip one?" All placeholder types contribute equally to the pain — no single worst type.
- **Current verification behavior:** Always double and triple checks everything — re-reads the entire prompt multiple times looking for leftover [BRACKETS] before sending.
- **Key insight:** There is no "easy mode" with the current approach. When it works, it's entirely because of the manual verification effort — not because the step was simpler. The process always requires the same cognitive tax.
- **Signal:** The manual copy-paste + file path lookup process is slow and error-prone

## Area 3: Current Situation Mapping
- **Methodology file location:** `/Users/enrique/Documents/Software Development/dev-workflow/dev-workflowWF/docs/Tailoring Methodology/State Capture/Tailoring_Methodology_state_capture.md`
- **Source files live in two distinct directory trees:**
  - `/Users/enrique/Documents/Software Development/dev-workflow/dev-workflowWF/` (WF variant)
  - `/Users/enrique/Documents/Software Development/dev-workflow/dev-workflow/` (non-WF variant)
  - Note: these are two different roots — `dev-workflow/dev-workflowWF/` vs `dev-workflow/dev-workflow/` (the WF suffix distinguishes them)
- **Current workflow:** Open methodology file → find step → copy template → manually hunt and replace each placeholder → double/triple verify → paste into Claude Code terminal

## Area 4: Impact and Urgency Assessment
- **Usage pattern:** Concentrated bursts when working on a new domain — not daily, but high volume when active
- **Impact:** When it hits, it hits hard — multiple steps in sequence, each requiring the same manual verification tax
- **User state:** Burned out from the current process — high motivation to solve
- **Urgency basis:** Personal pain + productivity bottleneck, not organizational pressure
- **Cost of inaction:** Every new domain triggers the same painful process with no improvement over time

## Area 5: Initial Boundary Identification
- **Clearly in scope:** The placeholder substitution workflow — extracting a template, filling all placeholders, verifying completeness, outputting ready-to-use prompt
- **Clearly out of scope:** The methodology creation process itself, the AI conversations that follow, the outputs those conversations produce
- **Primary system:** `Tailoring_Methodology_state_capture.md` + the two file system roots that feed placeholder values
- **No premature solution definition:** User had no preconceived solution — ideal state was defined collaboratively during assessment

## Area 6: Assessment Constraints, Resources, and Readiness
- **Who is conducting:** Solo practitioner (self-assessed)
- **Technical constraints:** None — no language restrictions, no missing tools, script can live anywhere
- **File system context:** Two known directory roots, user knows which files live where
- **Environment:** macOS, uses Claude Code (terminal/CLI), zsh shell
- **Assessment readiness:** Fully ready — situation is well-understood, boundaries are clear, no blockers

## Synthesis and Reflection Findings

**Situation framing (confirmed by user):**
> "The situation is clean and well-bounded. You have a documented 8-step process that works — the methodology itself isn't broken. What's broken is the mechanical interface between you and that process: extracting a template, substituting 3–8 placeholders of 5 semantic categories (paths, text blocks, names, lists, AI-feedback), and then carrying the full cognitive burden of verifying nothing was missed. Every new domain triggers the same tax, with no improvement built in. The pain is structural, not accidental."

**Key distinctions established:**
- The methodology ≠ the problem
- The interface between the methodology and its execution = the problem
- The verification burden is structural — it cannot be solved by trying harder
- Scope is tight: one source file, two directory roots, one workflow to replace

**Readiness confirmed by user:** "The problem is well described — and we did it."

**Additional context:** None surfaced.

---

## Final Readiness Assessment

**Signal:** Clearly identified, precisely described, no interpretation drift.
> Status: ✅ Signal identified and preserved in raw form

**Current situation documentation:** Fully mapped — workflow steps, placeholder types, file locations, pain source, usage pattern.
> Status: ✅ Comprehensive

**Fact-interpretation discipline:** Clean — the documented process works, the pain is specifically in the mechanical interface, no conflation between methodology problems and execution problems.
> Status: ✅ Rigorous separation maintained

**Impact and urgency:** Concentrated bursts, structural tax, user burned out — grounded in lived experience not assumption.
> Status: ✅ Evidence-based

**Investigation boundaries:** Tight and agreed — one file, two roots, one workflow to replace.
> Status: ✅ Clear boundaries, no ambiguity

**Assessment feasibility:** Solo practitioner, no technical constraints, fully ready.
> Status: ✅ Fully feasible

**Overall:** Situation assessment is complete and ready to move to solution design.
