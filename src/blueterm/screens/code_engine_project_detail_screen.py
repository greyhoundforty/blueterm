"""Code Engine project detail modal screen"""
from textual.app import ComposeResult
from textual.containers import Container, Vertical, VerticalScroll, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static
from textual.message import Message
from rich.text import Text
from rich.table import Table

from ..api.models import CodeEngineProject


class CodeEngineProjectDetailScreen(ModalScreen[None]):
    """
    Modal screen for displaying detailed Code Engine project information.

    Displays as a centered pop-over window with semi-transparent background.

    Keyboard:
        Enter: View project resources (apps, jobs, builds, secrets)
        Esc, x, or q: Close modal
    """

    # CSS for prominent centered modal
    DEFAULT_CSS = """
    CodeEngineProjectDetailScreen {
        align: center middle;
    }

    CodeEngineProjectDetailScreen > Container {
        width: 80%;
        height: 80%;
        background: $surface;
        border: heavy $primary;
    }
    """

    class ViewResources(Message):
        """Message sent when user wants to view project resources"""
        def __init__(self, project_id: str) -> None:
            self.project_id = project_id
            super().__init__()

    def __init__(self, project: CodeEngineProject, **kwargs):
        """
        Initialize detail screen

        Args:
            project: CodeEngineProject object to display details for
        """
        super().__init__(**kwargs)
        self.project = project

    def compose(self) -> ComposeResult:
        """Compose detail screen layout"""
        with Container(id="detail_dialog"):
            with Vertical(id="detail_content"):
                # Header with title and close hint
                with Horizontal(id="detail_header"):
                    yield Label(f"Code Engine Project: {self.project.name}", id="detail_title")
                    yield Label("Press Esc, x, or q to close", id="detail_close_hint")

                # Scrollable content area
                with VerticalScroll(id="detail_scroll"):
                    yield Static(self._format_details(), id="detail_info")

                # Action buttons
                with Horizontal(id="detail_buttons"):
                    yield Button("View Resources (Enter)", variant="success", id="view_resources_button")
                    yield Button("Close (Esc)", variant="primary", id="close_button")

    def _format_details(self) -> Table:
        """
        Format project details as a rich table

        Returns:
            Rich Table with project information
        """
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Field", style="cyan bold", width=20)
        table.add_column("Value", style="white")

        # Basic information
        table.add_row("Name", self.project.name)
        table.add_row("ID", self.project.id)

        # Status with color
        status_color_map = {
            "active": "green",
            "inactive": "red",
            "creating": "yellow",
            "deleting": "magenta",
            "failed": "red bold",
        }
        status_color = status_color_map.get(self.project.status.lower(), "white")
        status_text = Text(self.project.status, style=status_color)
        table.add_row("Status", status_text)

        # Location
        table.add_row("Region", self.project.region)
        table.add_row("Resource Group ID", self.project.resource_group_id)

        # Metadata
        table.add_row("Created", self.project.created_at)
        if self.project.entity_tag:
            table.add_row("Entity Tag", self.project.entity_tag)
        table.add_row("CRN", self.project.crn)

        # Resource counts
        table.add_section()
        table.add_row("", Text("Resources", style="yellow bold"))
        table.add_row("Applications", str(self.project.apps_count))
        table.add_row("Jobs", str(self.project.jobs_count))
        table.add_row("Builds", str(self.project.builds_count))
        table.add_row("Secrets", str(self.project.secrets_count))

        return table

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "view_resources_button":
            # Send message to parent app to load resources
            self.post_message(self.ViewResources(self.project.id))
            self.dismiss()
        else:
            # Close button
            self.dismiss()

    def on_key(self, event) -> None:
        """Handle keyboard events"""
        if event.key == "enter":
            # Enter key triggers View Resources
            self.post_message(self.ViewResources(self.project.id))
            self.dismiss()
        elif event.key in ("escape", "x", "q"):
            # Close modal
            self.dismiss()
