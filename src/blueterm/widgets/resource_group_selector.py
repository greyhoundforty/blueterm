"""Resource group selector widget"""
from typing import List, Optional

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, Button
from rich.text import Text

from ..api.models import ResourceGroup


class ResourceGroupSelector(Widget):
    """
    Resource group selector for top nav.

    Shows: Resource Group: <current> [Change]

    Click [Change] button to open selection modal
    """

    selected_resource_group: reactive[Optional[ResourceGroup]] = reactive(None)

    class ResourceGroupChanged(Message):
        """Message emitted when resource group selection changes"""
        def __init__(self, resource_group: ResourceGroup) -> None:
            self.resource_group = resource_group
            super().__init__()

    class ResourceGroupSelectionRequested(Message):
        """Message emitted when user requests to change resource group"""
        pass

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.resource_groups: List[ResourceGroup] = []
        self._selected_index: int = 0

    def compose(self) -> ComposeResult:
        """Compose resource group selector layout"""
        with Horizontal(id="resource_group_bar"):
            yield Label("  Resource Group: ", id="rg_label")
            yield Label("N/A", id="current_resource_group")
            yield Button("Change", variant="primary", id="change_rg_button")

    def set_resource_groups(self, resource_groups: List[ResourceGroup], selected: Optional[ResourceGroup] = None) -> None:
        """
        Set available resource groups and optionally select one

        Args:
            resource_groups: List of ResourceGroup objects
            selected: Initial resource group to select (defaults to first)
        """
        self.resource_groups = resource_groups
        if selected:
            self.selected_resource_group = selected
            self._selected_index = next(
                (i for i, rg in enumerate(resource_groups) if rg.id == selected.id),
                0
            )
        elif resource_groups:
            self.selected_resource_group = resource_groups[0]
            self._selected_index = 0

        self._update_display()

    def _update_display(self) -> None:
        """Update the resource group display"""
        if not self.resource_groups:
            return

        # Update current resource group label
        try:
            current_rg_label = self.query_one("#current_resource_group", Label)
            if self.selected_resource_group:
                current_rg_label.update(Text(self.selected_resource_group.name, style="bold green"))
        except:
            pass

    def select_next(self) -> None:
        """Select next resource group (g key)"""
        if not self.resource_groups:
            return

        self._selected_index = (self._selected_index + 1) % len(self.resource_groups)
        self._select_resource_group(self.resource_groups[self._selected_index])

    def select_previous(self) -> None:
        """Select previous resource group (G key)"""
        if not self.resource_groups:
            return

        self._selected_index = (self._selected_index - 1) % len(self.resource_groups)
        self._select_resource_group(self.resource_groups[self._selected_index])

    def _select_resource_group(self, resource_group: ResourceGroup) -> None:
        """
        Select a resource group and emit change message

        Args:
            resource_group: ResourceGroup to select
        """
        if self.selected_resource_group != resource_group:
            self.selected_resource_group = resource_group
            self._update_display()
            self.post_message(self.ResourceGroupChanged(resource_group))

    def watch_selected_resource_group(self, old_rg: Optional[ResourceGroup], new_rg: Optional[ResourceGroup]) -> None:
        """React to selected resource group changes (Textual reactive property)"""
        if new_rg:
            self._update_display()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle Change button press"""
        if event.button.id == "change_rg_button":
            # Emit message to request resource group selection
            self.post_message(self.ResourceGroupSelectionRequested())

    @property
    def resource_group_count(self) -> int:
        """Get number of available resource groups"""
        return len(self.resource_groups)
