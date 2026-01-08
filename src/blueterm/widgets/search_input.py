"""Search input widget for filtering instances"""
from textual.app import ComposeResult
from textual.containers import Container
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Label


class SearchInput(Widget):
    """
    Search input widget for filtering instances.

    Keyboard:
        /: Focus search input
        Esc: Clear search and unfocus
        Enter: Unfocus but keep search
    """

    DEFAULT_CLASSES = "hidden"

    class SearchChanged(Message):
        """Message emitted when search query changes"""
        def __init__(self, value: str) -> None:
            self.value = value
            super().__init__()

    class SearchCancelled(Message):
        """Message emitted when search is cancelled (Esc key)"""
        pass

    def compose(self) -> ComposeResult:
        """Compose search input layout"""
        with Container(id="search_container"):
            yield Label("Search: ", id="search_label")
            yield Input(
                placeholder="Filter instances by name or status...",
                id="search_field"
            )

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes"""
        self.post_message(self.SearchChanged(event.value))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key - unfocus but keep search"""
        self.query_one("#search_field", Input).blur()

    def on_key(self, event) -> None:
        """Handle keyboard events"""
        if event.key == "escape":
            self.clear_search()
            self.hide()
            self.post_message(self.SearchCancelled())
            event.prevent_default()
            event.stop()

    def show(self) -> None:
        """Show search input and focus"""
        self.remove_class("hidden")
        self.query_one("#search_field", Input).focus()

    def hide(self) -> None:
        """Hide search input"""
        self.add_class("hidden")

    def clear_search(self) -> None:
        """Clear search input value"""
        search_field = self.query_one("#search_field", Input)
        search_field.value = ""
        search_field.blur()
        self.post_message(self.SearchChanged(""))

    def focus_search(self) -> None:
        """Focus the search input"""
        self.show()
        self.query_one("#search_field", Input).focus()

    @property
    def is_visible(self) -> bool:
        """Check if search input is visible"""
        return not self.has_class("hidden")

    @property
    def search_value(self) -> str:
        """Get current search value"""
        return self.query_one("#search_field", Input).value
