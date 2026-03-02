"""Template Filler TUI — main application."""

from textual.app import App
from textual.binding import Binding

from template_filler_tui.config import METHODOLOGY_PATH, PLACEHOLDER_REGISTRY_PATH
from template_filler_tui.models.methodology import parse_methodology, Step
from template_filler_tui.models.placeholder import load_registry, PlaceholderInfo
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

    def on_mount(self) -> None:
        self.steps = parse_methodology(METHODOLOGY_PATH)
        self.registry = load_registry(PLACEHOLDER_REGISTRY_PATH)
        from template_filler_tui.screens.session_setup import SessionSetupScreen
        self.push_screen(SessionSetupScreen())


def main():
    app = TemplateFillerApp()
    app.run()
