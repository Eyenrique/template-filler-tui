"""Content Preview modal — scrollable read-only view of placeholder content."""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Static, Button, TextArea, Label
from textual.binding import Binding


class ContentPreviewScreen(ModalScreen):
    BINDINGS = [
        Binding("escape", "dismiss_preview", "Close"),
    ]

    def __init__(self, title: str, content: str, source_path: str | None = None):
        super().__init__()
        self.title_text = title
        self.content_text = content
        self.source_path = source_path

    def compose(self) -> ComposeResult:
        line_count = len(self.content_text.split("\n"))

        with Vertical(id="preview-modal"):
            with Horizontal(id="preview-modal-header"):
                with Vertical(id="preview-modal-info"):
                    yield Static(self.title_text, id="preview-modal-title", markup=False)
                    yield Label(f"{line_count} lines", id="preview-line-count")
                    if self.source_path:
                        yield Label(f"Source: {self.source_path}", id="preview-source-path")
                yield Button("X", variant="error", id="preview-close-btn")
            text_area = TextArea(id="preview-modal-content", read_only=True, show_line_numbers=True)
            text_area.text = self.content_text
            yield text_area

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "preview-close-btn":
            self.dismiss()

    def action_dismiss_preview(self) -> None:
        self.dismiss()
