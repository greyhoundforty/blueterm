"""Instance detail modal screen"""
from textual.app import ComposeResult
from textual.containers import Container, Vertical, VerticalScroll, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static
from rich.text import Text
from rich.panel import Panel
from rich.table import Table

from ..api.models import Instance


class DetailScreen(ModalScreen[None]):
    """
    Modal screen for displaying detailed instance information.

    Displays as a centered pop-over window with semi-transparent background.

    Keyboard:
        Enter, Esc, x, or q: Close modal
    """

    # CSS for prominent centered modal
    DEFAULT_CSS = """
    DetailScreen {
        align: center middle;
    }

    DetailScreen > Container {
        width: 80%;
        height: 80%;
        background: $surface;
        border: heavy $primary;
    }
    """

    def __init__(self, instance: Instance, **kwargs):
        """
        Initialize detail screen

        Args:
            instance: Instance object to display details for
        """
        super().__init__(**kwargs)
        self.instance = instance

    def compose(self) -> ComposeResult:
        """Compose detail screen layout"""
        with Container(id="detail_dialog"):
            with Vertical(id="detail_content"):
                # Header with title and close hint
                with Horizontal(id="detail_header"):
                    yield Label(f"Instance: {self.instance.name}", id="detail_title")
                    yield Label("Press Esc, x, or q to close", id="detail_close_hint")

                # Scrollable content area
                with VerticalScroll(id="detail_scroll"):
                    yield Static(self._format_details(), id="detail_info")

                # Close button
                with Horizontal(id="detail_buttons"):
                    yield Button("Close (Esc)", variant="primary", id="close_button")

    def _format_details(self) -> Table:
        """
        Format instance details as a rich table

        Returns:
            Rich Table with instance information
        """
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Field", style="cyan bold", width=20)
        table.add_column("Value", style="white")

        # Basic information
        table.add_row("Name", self.instance.name)
        table.add_row("ID", self.instance.id)
        table.add_row("Short ID", self.instance.short_id)

        # Status with color
        status_text = Text(
            f"{self.instance.status.symbol} {self.instance.status.value}",
            style=self.instance.status.color
        )
        table.add_row("Status", status_text)

        # Location
        table.add_row("Zone", self.instance.zone)

        # Network
        table.add_row("VPC Name", self.instance.vpc_name)
        table.add_row("VPC ID", self.instance.vpc_id)
        table.add_row("Primary IP", self.instance.primary_ip or "N/A")

        # Compute
        table.add_row("Profile", self.instance.profile)

        # Metadata
        table.add_row("Created", self.instance.created_at)
        table.add_row("CRN", self.instance.crn)

        # Action availability
        table.add_section()
        table.add_row("", Text("Available Actions", style="yellow bold"))
        table.add_row("Can Start", "✓" if self.instance.can_start else "✗")
        table.add_row("Can Stop", "✓" if self.instance.can_stop else "✗")
        table.add_row("Can Reboot", "✓" if self.instance.can_reboot else "✗")

        return table

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        self.dismiss()

    def on_key(self, event) -> None:
        """Handle keyboard events"""
        if event.key in ("enter", "escape", "x", "q"):
            self.dismiss()
