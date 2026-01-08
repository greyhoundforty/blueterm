"""Error display modal screen"""
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static
from rich.text import Text


class ErrorScreen(ModalScreen[None]):
    """
    Modal screen for displaying errors with optional recovery suggestions.

    Keyboard:
        Enter or Esc: Close modal
        q: Close modal
    """

    def __init__(
        self,
        error_message: str,
        title: str = "Error",
        recoverable: bool = True,
        suggestion: str = "",
        **kwargs
    ):
        """
        Initialize error screen

        Args:
            error_message: Error message to display
            title: Modal title (default: "Error")
            recoverable: Whether error is recoverable (affects button text)
            suggestion: Optional suggestion for recovery
        """
        super().__init__(**kwargs)
        self.error_message = error_message
        self.title_text = title
        self.recoverable = recoverable
        self.suggestion = suggestion

    def compose(self) -> ComposeResult:
        """Compose error screen layout"""
        with Container(id="error_dialog"):
            with Vertical(id="error_content"):
                # Title
                yield Label(self.title_text, id="error_title")

                # Error message
                error_text = Text(self.error_message, style="red")
                yield Static(error_text, id="error_message")

                # Suggestion (if provided)
                if self.suggestion:
                    suggestion_text = Text(self.suggestion, style="yellow italic")
                    yield Static(suggestion_text, id="error_suggestion")

                # Buttons
                with Container(id="error_buttons"):
                    if self.recoverable:
                        yield Button("OK", variant="primary", id="ok_button")
                    else:
                        yield Button("Exit", variant="error", id="exit_button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "exit_button":
            # Non-recoverable error - exit application
            self.app.exit(1)
        else:
            # Close modal
            self.dismiss()

    def on_key(self, event) -> None:
        """Handle keyboard events"""
        if event.key in ("enter", "escape", "q"):
            if not self.recoverable:
                self.app.exit(1)
            else:
                self.dismiss()
