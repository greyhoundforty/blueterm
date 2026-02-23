"""Inline split-pane detail panel widget.

Sits alongside the InstanceTable inside a horizontal container.
Hidden by default (display: none); shown when the user presses D.

This is the "split pane" alternative to the full-screen DetailScreen modal.
Both views show the same data — the user can try each and pick a favourite:
  d  →  Modal overlay  (DetailScreen)
  D  →  Inline split   (this widget, DetailPanel)
"""
from textual.widget import Widget
from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Label, Static
from rich.text import Text
from rich.table import Table

from ..api.models import Instance


class DetailPanel(Widget):
    """
    Inline detail panel shown alongside the instance table.

    When visible, the parent horizontal container gives this widget ~45 %
    of the width and the table keeps the remaining 55 %.

    Keyboard (when panel is focused):
        Esc or x  — close the panel and return focus to the table
    """

    DEFAULT_CSS = """
    DetailPanel {
        /* Hidden by default — takes no space */
        display: none;

        /* When visible, fills its share of the horizontal container */
        width: 45%;
        height: 100%;
        background: $surface;
        border-left: heavy $primary;
        padding: 0 1;
    }

    DetailPanel.visible {
        display: block;
    }

    /* ---- inner elements ---- */

    DetailPanel #detail_panel_header {
        height: 3;
        padding: 0 0 1 0;
        border-bottom: solid $primary-darken-1;
    }

    DetailPanel #detail_panel_title {
        text-style: bold;
        color: $primary;
        height: 1;
    }

    DetailPanel #detail_panel_close_hint {
        color: $text-muted;
        height: 1;
    }

    DetailPanel #detail_panel_scroll {
        height: 1fr;
    }

    DetailPanel #detail_panel_info {
        padding: 1 0;
    }
    """

    def __init__(self, **kwargs):
        """Initialise the panel in a hidden state."""
        super().__init__(**kwargs)
        self.current_instance: Instance | None = None

    def compose(self) -> ComposeResult:
        """Layout: header (title + hint) above a scrollable content area."""
        with Vertical(id="detail_panel_container"):
            # Header section
            with Vertical(id="detail_panel_header"):
                yield Label("", id="detail_panel_title")
                yield Label("Esc or x — close panel", id="detail_panel_close_hint")

            # Scrollable detail content
            with VerticalScroll(id="detail_panel_scroll"):
                yield Static("", id="detail_panel_info")

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def show_instance(self, instance: Instance) -> None:
        """
        Populate the panel with the given instance's details and make it visible.

        Args:
            instance: The Instance object to display.
        """
        self.current_instance = instance

        # Update title
        self.query_one("#detail_panel_title", Label).update(
            f"[bold]{instance.name}[/bold]"
        )

        # Render detail table and push to the static widget
        self.query_one("#detail_panel_info", Static).update(
            self._format_details(instance)
        )

        # Make visible (CSS class toggles display: block)
        self.add_class("visible")

        # Grab keyboard focus so Esc / x work immediately
        self.focus()

    def hide_panel(self) -> None:
        """Hide the panel and clear its content."""
        self.current_instance = None
        self.remove_class("visible")

    def can_focus(self) -> bool:
        """Allow focus only while visible so Tab doesn't land here when hidden."""
        return self.has_class("visible")

    # ------------------------------------------------------------------ #
    # Keyboard handling                                                    #
    # ------------------------------------------------------------------ #

    def on_key(self, event) -> None:
        """Close the panel on Esc or x."""
        if event.key in ("escape", "x"):
            self.hide_panel()
            # Return focus to the table
            try:
                self.app.query_one("#instance_table").focus()
            except Exception:
                pass
            event.stop()
            event.prevent_default()

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _format_details(self, instance: Instance) -> Table:
        """
        Build a Rich Table with two columns (field name | value).

        The table is injected into a Textual Static widget which renders
        Rich renderables natively.

        Args:
            instance: The Instance to format.

        Returns:
            A Rich Table ready for display.
        """
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Field", style="cyan bold", width=16)
        table.add_column("Value", style="white")

        # ---- Identity ----
        table.add_row("Name",     instance.name)
        table.add_row("ID",       instance.id)
        table.add_row("Short ID", instance.short_id)

        # ---- Status (coloured) ----
        status_text = Text(
            f"{instance.status.symbol} {instance.status.value}",
            style=instance.status.color,
        )
        table.add_row("Status", status_text)

        # ---- Location ----
        table.add_row("Zone", instance.zone)

        # ---- Network ----
        table.add_row("VPC Name",   instance.vpc_name)
        table.add_row("VPC ID",     instance.vpc_id)
        table.add_row("Private IP", instance.primary_ip or "N/A")

        # ---- Compute ----
        table.add_row("Profile", instance.profile)

        # ---- Metadata ----
        table.add_row("Created", instance.created_at)
        table.add_row("CRN",     instance.crn)

        # ---- Available actions ----
        table.add_section()
        table.add_row("", Text("Actions", style="yellow bold"))
        table.add_row("Start",  "✓" if instance.can_start  else "✗")
        table.add_row("Stop",   "✓" if instance.can_stop   else "✗")
        table.add_row("Reboot", "✓" if instance.can_reboot else "✗")

        return table
