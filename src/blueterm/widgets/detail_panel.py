"""Instance detail sliding panel widget"""
from textual.widget import Widget
from textual.app import ComposeResult
from textual.containers import Container, Vertical, VerticalScroll
from textual.widgets import Label, Static
from textual.reactive import reactive
from rich.text import Text
from rich.table import Table

from ..api.models import Instance


class DetailPanel(Widget):
    """
    Sliding panel for displaying detailed instance information.
    Slides in from the right side of the screen.

    Keyboard:
        Esc or x: Close panel
    """

    DEFAULT_CSS = """
    DetailPanel {
        dock: right;
        width: 50;
        background: $surface;
        border-left: heavy $primary;
        padding: 1;
        layer: overlay;
        offset-x: 100%;
        transition: offset 300ms;
    }

    DetailPanel.visible {
        offset-x: 0;
    }

    DetailPanel #detail_panel_header {
        height: auto;
        padding: 0 0 1 0;
        margin-bottom: 1;
        border-bottom: solid $primary;
    }

    DetailPanel #detail_panel_title {
        text-style: bold;
        color: $primary;
    }

    DetailPanel #detail_panel_close_hint {
        color: $text-muted;
        text-align: right;
    }

    DetailPanel #detail_panel_scroll {
        height: 1fr;
        border: none;
    }

    DetailPanel #detail_panel_info {
        padding: 0;
    }
    """

    visible = reactive(False)
    instance = reactive(None)

    def __init__(self, **kwargs):
        """Initialize detail panel"""
        super().__init__(**kwargs)
        self.current_instance = None

    def compose(self) -> ComposeResult:
        """Compose detail panel layout"""
        with Vertical(id="detail_panel_container"):
            # Header
            with Container(id="detail_panel_header"):
                yield Label("", id="detail_panel_title")
                yield Label("Press Esc or x to close", id="detail_panel_close_hint")

            # Scrollable content area
            with VerticalScroll(id="detail_panel_scroll"):
                yield Static("", id="detail_panel_info")

    def show_instance(self, instance: Instance) -> None:
        """
        Show detail panel with instance information

        Args:
            instance: Instance object to display details for
        """
        self.current_instance = instance
        self.visible = True

        # Update title
        title_label = self.query_one("#detail_panel_title", Label)
        title_label.update(f"Instance: {instance.name}")

        # Update content
        info_static = self.query_one("#detail_panel_info", Static)
        info_static.update(self._format_details(instance))

        # Add visible class for CSS
        self.add_class("visible")

        # Focus the panel so it receives keyboard events
        self.focus()

    def hide_panel(self) -> None:
        """Hide the detail panel"""
        self.visible = False
        self.current_instance = None
        self.remove_class("visible")

    def _format_details(self, instance: Instance) -> Table:
        """
        Format instance details as a rich table

        Args:
            instance: Instance object to format

        Returns:
            Rich Table with instance information
        """
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Field", style="cyan bold", width=18)
        table.add_column("Value", style="white")

        # Basic information
        table.add_row("Name", instance.name)
        table.add_row("ID", instance.id)
        table.add_row("Short ID", instance.short_id)

        # Status with color
        status_text = Text(
            f"{instance.status.symbol} {instance.status.value}",
            style=instance.status.color
        )
        table.add_row("Status", status_text)

        # Location
        table.add_row("Zone", instance.zone)

        # Network
        table.add_row("VPC Name", instance.vpc_name)
        table.add_row("VPC ID", instance.vpc_id)
        table.add_row("Primary IP", instance.primary_ip or "N/A")

        # Compute
        table.add_row("Profile", instance.profile)

        # Metadata
        table.add_row("Created", instance.created_at)
        table.add_row("CRN", instance.crn)

        # Action availability
        table.add_section()
        table.add_row("", Text("Available Actions", style="yellow bold"))
        table.add_row("Can Start", "✓" if instance.can_start else "✗")
        table.add_row("Can Stop", "✓" if instance.can_stop else "✗")
        table.add_row("Can Reboot", "✓" if instance.can_reboot else "✗")

        return table

    def on_key(self, event) -> None:
        """Handle keyboard events"""
        if event.key in ("escape", "x"):
            self.hide_panel()
            event.stop()
            event.prevent_default()

    def can_focus(self) -> bool:
        """Panel can receive focus when visible"""
        return self.visible
