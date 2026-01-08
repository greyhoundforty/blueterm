"""Confirmation dialog modal screen"""
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static
from rich.text import Text


class ConfirmScreen(ModalScreen[bool]):
    """
    Modal screen for confirming actions before execution.

    Returns True if confirmed, False if cancelled.

    Keyboard:
        y: Confirm
        n or Esc: Cancel
        Enter: Confirm (if focused on Yes button)
    """

    def __init__(
        self,
        title: str,
        message: str,
        confirm_label: str = "Yes",
        cancel_label: str = "No",
        **kwargs
    ):
        """
        Initialize confirmation screen

        Args:
            title: Confirmation title/question
            message: Detailed message explaining the action
            confirm_label: Label for confirm button (default: "Yes")
            cancel_label: Label for cancel button (default: "No")
        """
        super().__init__(**kwargs)
        self.title_text = title
        self.message_text = message
        self.confirm_label = confirm_label
        self.cancel_label = cancel_label

    def compose(self) -> ComposeResult:
        """Compose confirmation screen layout"""
        with Container(id="confirm_dialog"):
            with Vertical(id="confirm_content"):
                # Title
                yield Label(self.title_text, id="confirm_title")

                # Message
                message_text = Text(self.message_text, style="white")
                yield Static(message_text, id="confirm_message")

                # Buttons
                with Horizontal(id="confirm_buttons"):
                    yield Button(
                        self.confirm_label,
                        variant="success",
                        id="confirm_button"
                    )
                    yield Button(
                        self.cancel_label,
                        variant="default",
                        id="cancel_button"
                    )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "confirm_button":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def on_key(self, event) -> None:
        """Handle keyboard events"""
        if event.key == "y":
            self.dismiss(True)
        elif event.key in ("n", "escape"):
            self.dismiss(False)
