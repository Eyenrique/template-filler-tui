"""Template Fill screen — placeholder filling with live preview."""

import subprocess
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Static, Input, TextArea, Button, Label
from textual.binding import Binding

from template_filler_tui.models.methodology import Template
from template_filler_tui.models.placeholder import (
    find_tokens, classify_tokens, substitute, PlaceholderInfo, UIType,
)


COLLAPSE_THRESHOLD = 100  # lines


class TemplateFillScreen(Screen):
    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("ctrl+y", "copy_to_clipboard", "Copy to clipboard"),
        Binding("tab", "focus_next", "Next", show=False),
    ]

    def __init__(self, template: Template, step_label: str = ""):
        super().__init__()
        self.template = template
        self.step_label = step_label
        self.values: dict[str, str] = {}
        self.fillable: list[PlaceholderInfo] = []
        self.structural: list[str] = []
        self.current_idx = 0

    def compose(self) -> ComposeResult:
        # Classify placeholders
        tokens = find_tokens(self.template.text)
        self.fillable, self.structural = classify_tokens(tokens, self.app.registry)

        # Pre-fill from memory
        for p in self.fillable:
            remembered = self.app.memory.get(p.name)
            if remembered:
                self.values[p.name] = remembered

        with Vertical(id="template-fill"):
            # Header
            header_text = self.step_label
            if self.template.label != "default":
                header_text += f"  [{self.template.label}]"
            yield Static(header_text, id="fill-header")

            # Body: template + preview
            with Horizontal(id="fill-body"):
                with Vertical(id="template-panel"):
                    yield Static("Template", markup=False)
                    tmpl_display = Static(
                        self._render_template(),
                        id="template-display",
                        markup=False,
                    )
                    yield tmpl_display
                with Vertical(id="preview-panel"):
                    yield Static("Preview", markup=False)
                    prev_display = Static(
                        self._render_preview(),
                        id="preview-display",
                        markup=False,
                    )
                    yield prev_display

            # Input panel
            with Vertical(id="input-panel"):
                if self.fillable:
                    p = self._current_placeholder()
                    yield self._build_input_widgets(p)
                else:
                    yield Static("No placeholders to fill — template is ready.")
                    yield Button("Copy to Clipboard", variant="success", id="copy-btn")

            # Footer
            unfilled = self._unfilled_count()
            status = f" {len(self.fillable) - unfilled}/{len(self.fillable)} filled"
            status += "  |  Ctrl+Y: Copy  |  Tab: Next  |  Esc: Back"
            yield Static(status, id="fill-footer")

    def _current_placeholder(self) -> PlaceholderInfo:
        # Find next unfilled, or wrap to first unfilled
        for i in range(len(self.fillable)):
            idx = (self.current_idx + i) % len(self.fillable)
            if self.fillable[idx].name not in self.values:
                self.current_idx = idx
                return self.fillable[idx]
        # All filled — show the current one
        return self.fillable[self.current_idx % len(self.fillable)]

    def _unfilled_count(self) -> int:
        return sum(1 for p in self.fillable if p.name not in self.values)

    def _build_input_widgets(self, p: PlaceholderInfo) -> Vertical:
        """Build input widgets for the current placeholder."""
        container = Vertical()
        remembered = self.values.get(p.name)

        name_label = Label(f"[{p.name}]", classes="placeholder-name", markup=False)
        desc_label = Label(p.description, classes="placeholder-desc", markup=False)

        if p.ui_type in (UIType.TEXT, UIType.AI_FEEDBACK, UIType.LIST):
            hint = "Enter file path to read content, or paste text directly"
            if remembered:
                display = remembered if len(remembered) <= 80 else remembered[:77] + "..."
                hint = f"Remembered: {display}  (Enter to reuse)"
            input_widget = TextArea(id="value-input")
            input_widget.styles.height = 4
        else:
            hint = "Enter value"
            if p.ui_type == UIType.PATH:
                hint = "Enter file/directory path"
            elif p.ui_type == UIType.NAME:
                hint = "Enter name"
            if remembered:
                display = remembered if len(remembered) <= 80 else remembered[:77] + "..."
                hint = f"Remembered: {display}  (Enter to reuse)"
            initial_value = "@" if p.ui_type == UIType.PATH and not remembered else ""
            input_widget = Input(
                value=initial_value,
                placeholder=hint,
                id="value-input",
            )

        confirm_btn = Button("Confirm", variant="primary", id="confirm-btn")
        skip_btn = Button("Skip", id="skip-btn")

        container._nodes = [name_label, desc_label, input_widget]
        # Use compose_add_child pattern
        return Vertical(
            name_label,
            desc_label,
            input_widget,
            Horizontal(confirm_btn, skip_btn),
            id="input-area",
        )

    def _render_template(self) -> str:
        """Render template with placeholder status indicators."""
        text = self.template.text
        for p in self.fillable:
            token = f"[{p.name}]"
            if p.name in self.values:
                # Show as filled
                text = text.replace(token, f"✓{{{p.name}}}")
            # else: leave as-is (unfilled)

        for s in self.structural:
            # Structural tokens stay visible but dimmed
            pass  # they remain as-is in the text

        return text

    def _render_preview(self) -> str:
        """Render preview with values substituted, large values collapsed."""
        preview_values = {}
        for name, value in self.values.items():
            lines = value.split("\n")
            if len(lines) > COLLAPSE_THRESHOLD:
                # Collapse large values
                short = value[:60].replace("\n", " ")
                preview_values[name] = f"[{name} -> {len(lines)} lines: {short}...]"
            else:
                preview_values[name] = value

        return substitute(self.template.text, preview_values)

    def _update_displays(self) -> None:
        """Refresh template and preview displays."""
        self.query_one("#template-display", Static).update(
            self._render_template()
        )
        self.query_one("#preview-display", Static).update(
            self._render_preview()
        )
        unfilled = self._unfilled_count()
        status = f" {len(self.fillable) - unfilled}/{len(self.fillable)} filled"
        status += "  |  Ctrl+Y: Copy  |  Tab: Next  |  Esc: Back"
        self.query_one("#fill-footer", Static).update(status)

    async def _accept_value(self, value: str) -> None:
        """Accept a value for the current placeholder."""
        p = self.fillable[self.current_idx % len(self.fillable)]

        # For TEXT/AI_FEEDBACK/LIST: if value looks like a file path, read it
        if p.ui_type in (UIType.TEXT, UIType.AI_FEEDBACK, UIType.LIST):
            stripped = value.strip()
            if len(stripped) < 1024 and "\n" not in stripped:
                path = Path(stripped).expanduser()
                if path.exists() and path.is_file():
                    value = path.read_text(encoding="utf-8").strip()

        self.values[p.name] = value

        # Save to memory (session level by default)
        self.app.memory.set_session(p.name, value)

        # Move to next unfilled
        self.current_idx += 1
        await self._refresh_input()
        self._update_displays()

    async def _refresh_input(self) -> None:
        """Rebuild the input panel for the next placeholder."""
        input_panel = self.query_one("#input-panel", Vertical)
        await input_panel.remove_children()

        if self._unfilled_count() == 0:
            copy_btn = Button("Copy to Clipboard", variant="success", id="copy-btn")
            await input_panel.mount(
                Vertical(
                    Static("All placeholders filled!"),
                    copy_btn,
                )
            )
            copy_btn.focus()
        else:
            p = self._current_placeholder()
            new_input = self._build_input_widgets(p)
            await input_panel.mount(new_input)
            self.set_timer(0.1, self._focus_input)

    def _focus_input(self) -> None:
        """Focus the value input after a short delay."""
        try:
            self.query_one("#value-input").focus()
        except Exception:
            pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm-btn":
            widget = self.query_one("#value-input")
            if isinstance(widget, TextArea):
                value = widget.text.strip()
            elif isinstance(widget, Input):
                value = widget.value.strip()
            else:
                self.notify(f"Unknown widget type: {type(widget)}", severity="error")
                return

            if not value:
                p = self.fillable[self.current_idx % len(self.fillable)]
                remembered = self.values.get(p.name) or self.app.memory.get(p.name)
                if remembered:
                    value = remembered
                else:
                    self.notify("Please enter a value.", severity="warning")
                    return

            await self._accept_value(value)

        elif event.button.id == "copy-btn":
            self.action_copy_to_clipboard()

        elif event.button.id == "skip-btn":
            self.current_idx += 1
            await self._refresh_input()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in Input widget."""
        if event.input.id == "value-input":
            value = event.value.strip()
            p = self.fillable[self.current_idx % len(self.fillable)]
            if not value:
                remembered = self.values.get(p.name) or self.app.memory.get(p.name)
                if remembered:
                    value = remembered
                else:
                    return
            await self._accept_value(value)

    def action_copy_to_clipboard(self) -> None:
        """Copy the fully expanded result to clipboard."""
        result = substitute(self.template.text, self.values)
        try:
            subprocess.run(
                ["pbcopy"], input=result.encode("utf-8"), check=True
            )
            self.notify("Copied to clipboard!", severity="information")
        except Exception as e:
            self.notify(f"Copy failed: {e}", severity="error")

    def action_go_back(self) -> None:
        self.app.memory.save()
        self.app.pop_screen()
