"""Template Filler TUI — main application."""

import subprocess

from textual.app import App
from textual.binding import Binding

from template_filler_tui.config import METHODOLOGY_PATH, PLACEHOLDER_REGISTRY_PATH
from template_filler_tui.models.methodology import parse_methodology, Step
from template_filler_tui.models.placeholder import load_registry, find_unregistered_placeholders, PlaceholderInfo
from template_filler_tui.models.memory import Memory


class TemplateFillerApp(App):
    TITLE = "Template Filler"
    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.steps: list[Step] = []
        self.registry: dict[str, PlaceholderInfo] = {}
        self.memory = Memory()

    def copy_to_clipboard(self, text: str) -> None:
        """Override Textual's default OSC 52 clipboard with pbcopy for macOS."""
        self._clipboard = text
        try:
            subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
            self.notify("Selection copied!", severity="information")
        except Exception:
            super().copy_to_clipboard(text)

    def on_mount(self) -> None:
        self.steps = parse_methodology(METHODOLOGY_PATH)
        self.registry = load_registry(PLACEHOLDER_REGISTRY_PATH)

        from template_filler_tui.screens.session_setup import SessionSetupScreen
        self.push_screen(SessionSetupScreen())

        # Check for methodology/registry sync issues (pushed on top of session setup)
        unregistered = find_unregistered_placeholders(self.steps, self.registry)
        if unregistered:
            from template_filler_tui.screens.unregistered_warning import UnregisteredWarningScreen
            self.push_screen(UnregisteredWarningScreen(unregistered))


def main():
    app = TemplateFillerApp()
    app.run()
