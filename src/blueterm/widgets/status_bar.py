"""Status bar widget for displaying statistics and messages"""
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label
from rich.text import Text


class StatusBar(Widget):
    """
    Status bar displaying instance statistics and status messages.

    Shows: Total instances, running count, stopped count, loading indicator, messages
    """

    total_instances: reactive[int] = reactive(0)
    running_instances: reactive[int] = reactive(0)
    stopped_instances: reactive[int] = reactive(0)
    is_loading: reactive[bool] = reactive(False)
    message: reactive[str] = reactive("")
    message_type: reactive[str] = reactive("info")  # info, success, error, warning

    def compose(self) -> ComposeResult:
        """Compose status bar layout"""
        yield Label("", id="status_text")

    def watch_total_instances(self) -> None:
        """Update status bar when instance counts change"""
        self._update_display()

    def watch_running_instances(self) -> None:
        """Update status bar when running count changes"""
        self._update_display()

    def watch_stopped_instances(self) -> None:
        """Update status bar when stopped count changes"""
        self._update_display()

    def watch_is_loading(self) -> None:
        """Update status bar when loading state changes"""
        self._update_display()

    def watch_message(self) -> None:
        """Update status bar when message changes"""
        self._update_display()

    def _update_display(self) -> None:
        """Update the status bar text"""
        parts = []

        # Loading indicator
        if self.is_loading:
            parts.append(Text("⟳ Loading...", style="yellow"))

        # Instance statistics
        if self.total_instances > 0:
            stats = Text()
            stats.append(f"Total: {self.total_instances}", style="white")
            stats.append(" | ")
            stats.append(f"● Running: {self.running_instances}", style="green")
            stats.append(" | ")
            stats.append(f"○ Stopped: {self.stopped_instances}", style="red")
            parts.append(stats)

        # Status message
        if self.message:
            style_map = {
                "info": "blue",
                "success": "green",
                "error": "red bold",
                "warning": "yellow"
            }
            style = style_map.get(self.message_type, "white")
            parts.append(Text(f" | {self.message}", style=style))

        # Combine all parts
        if parts:
            combined = Text()
            for i, part in enumerate(parts):
                if i > 0:
                    combined.append("  ")
                combined.append(part)

            label = self.query_one("#status_text", Label)
            label.update(combined)
        else:
            label = self.query_one("#status_text", Label)
            label.update(Text("Ready", style="dim"))

    def update_stats(self, total: int, running: int, stopped: int) -> None:
        """
        Update instance statistics

        Args:
            total: Total number of instances
            running: Number of running instances
            stopped: Number of stopped instances
        """
        self.total_instances = total
        self.running_instances = running
        self.stopped_instances = stopped

    def set_loading(self, loading: bool) -> None:
        """
        Set loading state

        Args:
            loading: True if loading, False otherwise
        """
        self.is_loading = loading
        if loading:
            self.message = ""

    def set_message(self, message: str, message_type: str = "info") -> None:
        """
        Set status message

        Args:
            message: Message to display
            message_type: Type of message (info, success, error, warning)
        """
        self.message = message
        self.message_type = message_type

        # Auto-clear success/info messages after 5 seconds
        if message_type in ("success", "info"):
            self.set_timer(5.0, self.clear_message)

    def clear_message(self) -> None:
        """Clear the status message"""
        self.message = ""
