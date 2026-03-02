"""Session Setup screen — domain, phase, directory roots."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static


class SessionSetupScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        with Vertical(id="session-setup"):
            yield Static("Template Filler", classes="title")
            yield Label("Domain (e.g., UX, PM, Problem Definition):")
            yield Input(placeholder="Domain", id="domain-input")
            yield Label("Phase (e.g., Phase 0, Phase 3):")
            yield Input(placeholder="Phase", id="phase-input")
            yield Button("Start Session", variant="primary", id="start-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start-btn":
            domain = self.query_one("#domain-input", Input).value.strip()
            phase = self.query_one("#phase-input", Input).value.strip()

            if not domain or not phase:
                self.notify("Please fill in both domain and phase.", severity="error")
                return

            from template_filler_tui.screens.step_browser import StepBrowserScreen
            self.app.switch_screen(StepBrowserScreen())
