"""Unregistered Placeholders warning modal — selectable/copyable list."""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Static, Button, TextArea
from textual.binding import Binding


class UnregisteredWarningScreen(ModalScreen):
    BINDINGS = [
        Binding("escape", "dismiss_warning", "Close"),
    ]

    def __init__(self, names: list[str]):
        super().__init__()
        self.names = names

    def compose(self) -> ComposeResult:
        content = "\n".join(f"[{name}]" for name in self.names)

        with Vertical(id="unregistered-modal"):
            with Horizontal(id="unregistered-modal-header"):
                yield Static(
                    f"Unregistered Placeholders ({len(self.names)})",
                    id="unregistered-modal-title",
                )
                yield Button("X", variant="error", id="unregistered-close-btn")
            yield Static(
                "These placeholders appear in the methodology but are not in the registry.\n"
                "Update the Placeholder Registry or the methodology file.",
                id="unregistered-modal-hint",
            )
            text_area = TextArea(
                id="unregistered-modal-content",
                read_only=True,
                show_line_numbers=True,
            )
            text_area.text = content
            yield text_area

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "unregistered-close-btn":
            self.dismiss()

    def action_dismiss_warning(self) -> None:
        self.dismiss()
