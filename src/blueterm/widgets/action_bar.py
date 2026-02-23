"""Contextual action bar widget.

Shows service-specific keyboard shortcuts when a row is selected in the table.
Hidden entirely when no row is selected, so it doesn't waste screen space.
"""
from typing import Optional, List, Tuple

from rich.text import Text
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label

from ..api.models import Instance, InstanceStatus


# Each action is a (key_label, action_label, available) tuple.
# 'available' is True when the action can be performed; False dims the key hint.
Action = Tuple[str, str, bool]


def _vpc_actions(instance: Instance) -> List[Action]:
    """
    Build the action list for a VPC instance.

    VPC actions are state-aware: Start/Stop/Reboot are greyed out
    when they don't apply to the current instance status.
    """
    return [
        # (key, label, is_available)
        ("s", "Start",    instance.can_start),
        ("S", "Stop",     instance.can_stop),
        ("b", "Reboot",   instance.can_reboot),
        ("d", "Details",  True),
        ("D", "Split",    True),
    ]


def _iks_actions(_instance: Instance) -> List[Action]:
    """Build the action list for an IKS cluster."""
    return [
        ("d", "Details",    True),
        ("D", "Split",      True),
        ("w", "Workers",    True),
        ("k", "Kubeconfig", True),
    ]


def _roks_actions(_instance: Instance) -> List[Action]:
    """Build the action list for a ROKS (OpenShift) cluster."""
    return [
        ("d", "Details",   True),
        ("D", "Split",     True),
        ("w", "Workers",   True),
        ("k", "Kubeconfig",True),
        ("o", "Console",   True),
    ]


def _code_engine_project_actions(_instance: Instance) -> List[Action]:
    """Build the action list for a Code Engine project (top-level list)."""
    return [
        ("↵", "Open",    True),
        ("d", "Details", True),
        ("D", "Split",   True),
    ]


def _code_engine_resource_actions(_instance: Instance) -> List[Action]:
    """
    Build the action list for resources inside a Code Engine project
    (apps, jobs, builds, secrets).
    """
    return [
        ("d",   "Details", True),
        ("l",   "Logs",    True),
        ("u",   "Update",  True),
        ("Esc", "Back",    True),
    ]


class ActionBar(Widget):
    """
    A single-line bar that shows contextual keyboard shortcuts for the
    currently selected row.

    Usage:
        bar = ActionBar(id="action_bar")

        # When a row is highlighted:
        bar.update_context(resource_type_str, instance, inside_project=False)

        # When selection is cleared:
        bar.clear_context()

    The bar hides itself (display: none) when no instance is selected,
    so it does not consume vertical space.
    """

    DEFAULT_CSS = """
    ActionBar {
        height: 1;
        background: $panel;
        border-top: solid $primary-darken-1;
        padding: 0 2;
        display: none;
    }

    ActionBar.has-selection {
        display: block;
    }

    #action_bar_label {
        height: 1;
        content-align: left middle;
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        """Render as a single label that we update reactively."""
        yield Label("", id="action_bar_label")

    def update_context(
        self,
        resource_type: str,
        instance: Instance,
        inside_project: bool = False,
    ) -> None:
        """
        Populate the bar with actions appropriate for the given resource.

        Args:
            resource_type: One of "vpc", "iks", "roks", "code_engine"
            instance:      The currently selected Instance object
            inside_project: For Code Engine only — True when the user has
                            drilled into a project and is viewing apps/jobs/etc.
        """
        # Pick the right action list based on service type
        if resource_type == "vpc":
            actions = _vpc_actions(instance)
        elif resource_type == "iks":
            actions = _iks_actions(instance)
        elif resource_type == "roks":
            actions = _roks_actions(instance)
        elif resource_type == "code_engine":
            if inside_project:
                actions = _code_engine_resource_actions(instance)
            else:
                actions = _code_engine_project_actions(instance)
        else:
            actions = []

        # Build a Rich Text string: "[key] Label  [key] Label  ..."
        line = Text()
        for i, (key, label, available) in enumerate(actions):
            if i > 0:
                line.append("   ", style="dim")  # separator between actions

            if available:
                # Bright key hint + normal label
                line.append(f"[{key}]", style="bold cyan")
                line.append(f" {label}", style="white")
            else:
                # Dim everything when the action is not currently applicable
                line.append(f"[{key}]", style="dim")
                line.append(f" {label}", style="dim")

        # Update the label and make the bar visible
        label_widget = self.query_one("#action_bar_label", Label)
        label_widget.update(line)
        self.add_class("has-selection")

    def clear_context(self) -> None:
        """
        Hide the action bar.

        Called when the table has no rows or the cursor leaves the table.
        """
        self.remove_class("has-selection")
        label_widget = self.query_one("#action_bar_label", Label)
        label_widget.update("")
