"""Resource type selector widget for left sidebar"""
from enum import Enum
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static
from rich.text import Text


class ResourceType(Enum):
    """Available resource types"""
    VPC = "VPC"
    IKS = "IKS"
    ROKS = "ROKS"
    CODE_ENGINE = "Code Engine"


class ResourceTypeSelector(Widget):
    """
    Left sidebar for selecting resource type.

    Resource Types:
        VPC: Virtual Private Cloud instances
        IKS: IBM Kubernetes Service clusters
        ROKS: Red Hat OpenShift on IBM Cloud clusters
        Code Engine: Serverless apps, jobs, and functions

    Keyboard Navigation:
        v: Switch to VPC
        i: Switch to IKS
        r: Switch to ROKS
        c: Switch to Code Engine
        j/k or ↑/↓: Navigate through resource types
    """

    selected_type: reactive[ResourceType] = reactive(ResourceType.VPC)

    class ResourceTypeChanged(Message):
        """Message emitted when resource type selection changes"""
        def __init__(self, resource_type: ResourceType) -> None:
            self.resource_type = resource_type
            super().__init__()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._selected_index: int = 0
        self._resource_types = list(ResourceType)
        self._visible: bool = True

    def compose(self) -> ComposeResult:
        """Compose vertical sidebar layout"""
        with Vertical(id="resource_type_panel"):
            # Title
            yield Static("[bold cyan]RESOURCES[/bold cyan]", id="resource_type_title")

            # Resource type list
            yield Static("", id="resource_type_list")

    def on_mount(self) -> None:
        """Update display when mounted"""
        self._update_display()

    def _update_display(self) -> None:
        """Update the resource type list display"""
        resource_list_static = self.query_one("#resource_type_list", Static)
        resource_text = Text()

        # Display each resource type
        for idx, resource_type in enumerate(self._resource_types):
            is_selected = (idx == self._selected_index)

            # Get shortcut key (numbers: 1, 2, 3, 4)
            shortcuts = {
                ResourceType.VPC: "1",
                ResourceType.IKS: "2",
                ResourceType.ROKS: "3",
                ResourceType.CODE_ENGINE: "4",
            }
            shortcut = shortcuts.get(resource_type, "")

            # Format: [1] VPC ◀ (selected) or [1] VPC (not selected)
            if is_selected:
                resource_text.append(f"[{shortcut}] ", style="bold cyan")
                resource_text.append(resource_type.value, style="bold green on #2ecc71")
                resource_text.append(" ◀", style="bold yellow")
            else:
                resource_text.append(f"[{shortcut}] ", style="dim")
                resource_text.append(resource_type.value, style="white")

            if idx < len(self._resource_types) - 1:
                resource_text.append("\n\n")

        resource_list_static.update(resource_text)

    def select_by_key(self, key: str) -> None:
        """
        Select resource type by keyboard shortcut

        Args:
            key: Keyboard shortcut ('1', '2', '3', '4')
        """
        key_map = {
            "1": ResourceType.VPC,
            "2": ResourceType.IKS,
            "3": ResourceType.ROKS,
            "4": ResourceType.CODE_ENGINE,
            # Legacy letter support (for backward compatibility)
            "v": ResourceType.VPC,
            "i": ResourceType.IKS,
            "o": ResourceType.ROKS,
            "r": ResourceType.ROKS,
            "c": ResourceType.CODE_ENGINE,
        }

        if key in key_map:
            resource_type = key_map[key]
            self._selected_index = self._resource_types.index(resource_type)
            self._select_type(resource_type)

    def select_next(self) -> None:
        """Select next resource type (down/j key)"""
        self._selected_index = (self._selected_index + 1) % len(self._resource_types)
        self._select_type(self._resource_types[self._selected_index])

    def select_previous(self) -> None:
        """Select previous resource type (up/k key)"""
        self._selected_index = (self._selected_index - 1) % len(self._resource_types)
        self._select_type(self._resource_types[self._selected_index])

    def _select_type(self, resource_type: ResourceType) -> None:
        """
        Select a resource type and emit change message

        Args:
            resource_type: ResourceType to select
        """
        if self.selected_type != resource_type:
            self.selected_type = resource_type
            self._update_display()
            self.post_message(self.ResourceTypeChanged(resource_type))

    def watch_selected_type(self, old_type: ResourceType, new_type: ResourceType) -> None:
        """React to selected type changes (Textual reactive property)"""
        self._update_display()
    
    def toggle_visibility(self) -> None:
        """Toggle sidebar visibility"""
        self._visible = not self._visible
        if self._visible:
            self.display = True
            self.remove_class("hidden")
        else:
            self.display = False
            self.add_class("hidden")
    
    @property
    def visible(self) -> bool:
        """Check if sidebar is visible"""
        return self._visible