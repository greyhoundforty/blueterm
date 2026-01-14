"""Top navigation widget with 3-column layout: Resource Type | Regions | Resource Group"""
from typing import List, Optional

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static, Label
from rich.text import Text
from icecream import ic

from ..api.models import Region, ResourceGroup
from .resource_type_selector import ResourceType


class TopNavigation(Widget):
    """
    3-column top navigation bar:

    Column 1: Resource Type Selector (VPC/IKS/ROKS/Code Engine)
    Column 2: Region Selector (2 rows)
    Column 3: Resource Group Selector (scrollable box)

    Keyboard Navigation:
        1-4: Switch resource type
        r: Focus regions
        g: Focus resource groups
        h/l or Left/Right: Navigate within focused section
        0, 5-9: Jump to region by number (when focused)
    """

    selected_region: reactive[Optional[Region]] = reactive(None)
    selected_resource_group: reactive[Optional[ResourceGroup]] = reactive(None)
    selected_resource_type: reactive[ResourceType] = reactive(ResourceType.VPC)

    class RegionChanged(Message):
        """Message emitted when region selection changes"""
        def __init__(self, region: Region) -> None:
            self.region = region
            super().__init__()

    class ResourceGroupChanged(Message):
        """Message emitted when resource group selection changes"""
        def __init__(self, resource_group: ResourceGroup) -> None:
            self.resource_group = resource_group
            super().__init__()

    class ResourceTypeChanged(Message):
        """Message emitted when resource type selection changes"""
        def __init__(self, resource_type: ResourceType) -> None:
            self.resource_type = resource_type
            super().__init__()

    class ResourceGroupSelectionRequested(Message):
        """Message emitted when user requests to change resource group"""
        pass

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.regions: List[Region] = []
        self.resource_groups: List[ResourceGroup] = []
        self._region_index: int = 0
        self._resource_group_index: int = 0
        self._resource_type_index: int = 0
        self._resource_types = list(ResourceType)

        # Focus state
        self._region_focused: bool = False
        self._resource_group_focused: bool = False

        # Display info
        self.total_instances: int = 0
        self.running_instances: int = 0
        self.stopped_instances: int = 0
        self.resource_type_display: str = "VPC Instances"

    def compose(self) -> ComposeResult:
        """Compose the 3-column navigation layout"""
        with Horizontal(id="top_nav"):
            # Column 1: Resource Type Selector
            with Vertical(id="resource_type_column"):
                yield Label("[1]VPC [2]IKS", id="resource_type_label")
                yield Static("", id="resource_type_display")

            # Column 2: Region Selector (2 rows)
            with Vertical(id="region_column"):
                yield Label("", id="region_label")
                yield Static("", id="region_row_1")
                yield Static("", id="region_row_2")

            # Column 3: Resource Group Selector
            with Vertical(id="resource_group_column"):
                yield Label("", id="rg_label")
                yield Static("", id="resource_group_list")

    def on_mount(self) -> None:
        """Initialize display on mount"""
        ic("TopNavigation mounted")
        self.call_after_refresh(self._update_display)

    def _update_display(self) -> None:
        """Update all three columns"""
        if not self.is_mounted:
            return

        self._update_resource_type_display()
        self._update_region_display()
        self._update_resource_group_display()

    def _update_resource_type_display(self) -> None:
        """Update the resource type selector column"""
        try:
            # Update label with keyboard shortcuts
            label = self.query_one("#resource_type_label", Label)
            label_text = Text()
            label_text.append("[", style="dim")
            label_text.append("1-4", style="bold cyan")
            label_text.append("] ", style="dim")
            label_text.append("Resource", style="bold cyan")
            label.update(label_text)

            # Update resource type list
            display = self.query_one("#resource_type_display", Static)
            text = Text()

            for idx, rt in enumerate(self._resource_types):
                is_selected = (idx == self._resource_type_index)
                shortcut = str(idx + 1)

                if is_selected:
                    text.append(f"[{shortcut}]", style="bold cyan")
                    text.append(f"{rt.value}", style="bold green on #262626")
                else:
                    text.append(f"[{shortcut}]", style="dim")
                    text.append(f"{rt.value}", style="dim white")

                # 2 per row
                if idx == 1:
                    text.append("\n")
                elif idx < len(self._resource_types) - 1:
                    text.append(" ")

            display.update(text)
        except Exception as e:
            ic(f"Error updating resource type display: {e}")

    def _update_region_display(self) -> None:
        """Update the region selector column (2 rows)"""
        try:
            # Update label
            label = self.query_one("#region_label", Label)
            if self._region_focused:
                label_text = Text()
                label_text.append(">> ", style="bold yellow on #0f62fe")
                label_text.append("[R]egion", style="bold yellow on #0f62fe")
                label_text.append(" <<", style="bold yellow on #0f62fe")
            else:
                label_text = Text()
                label_text.append("[", style="dim")
                label_text.append("R", style="bold cyan")
                label_text.append("]egion", style="dim")
            label.update(label_text)

            # Update region rows
            row1 = self.query_one("#region_row_1", Static)
            row2 = self.query_one("#region_row_2", Static)

            if not self.regions:
                row1.update("No regions")
                row2.update("")
                return

            # Split regions into 2 rows
            mid = (len(self.regions) + 1) // 2
            regions_row1 = self.regions[:mid]
            regions_row2 = self.regions[mid:]

            # Build row 1
            text1 = Text()
            for idx, region in enumerate(regions_row1):
                is_selected = (idx == self._region_index)
                if is_selected:
                    if self._region_focused:
                        text1.append(f" {region.name} ", style="bold yellow on #0f62fe")
                    else:
                        text1.append(f" {region.name} ", style="bold green on #262626")
                else:
                    text1.append(f" {region.name} ", style="dim white")
                if idx < len(regions_row1) - 1:
                    text1.append("│", style="dim")
            row1.update(text1)

            # Build row 2
            text2 = Text()
            for idx, region in enumerate(regions_row2):
                actual_idx = mid + idx
                is_selected = (actual_idx == self._region_index)
                if is_selected:
                    if self._region_focused:
                        text2.append(f" {region.name} ", style="bold yellow on #0f62fe")
                    else:
                        text2.append(f" {region.name} ", style="bold green on #262626")
                else:
                    text2.append(f" {region.name} ", style="dim white")
                if idx < len(regions_row2) - 1:
                    text2.append("│", style="dim")
            row2.update(text2)

        except Exception as e:
            ic(f"Error updating region display: {e}")

    def _update_resource_group_display(self) -> None:
        """Update the resource group selector column"""
        try:
            # Update label
            label = self.query_one("#rg_label", Label)
            if self._resource_group_focused:
                label_text = Text()
                label_text.append(">> ", style="bold yellow on #0f62fe")
                label_text.append("[G]roup", style="bold yellow on #0f62fe")
                label_text.append(" <<", style="bold yellow on #0f62fe")
            else:
                label_text = Text()
                label_text.append("[", style="dim")
                label_text.append("G", style="bold cyan")
                label_text.append("]roup", style="dim")
            label.update(label_text)

            # Update resource group list
            rg_list = self.query_one("#resource_group_list", Static)

            if not self.resource_groups:
                rg_list.update("No groups")
                return

            text = Text()
            for idx, rg in enumerate(self.resource_groups):
                is_selected = (self.selected_resource_group and
                              rg.id == self.selected_resource_group.id)
                if is_selected:
                    if self._resource_group_focused:
                        text.append(f"● {rg.name}", style="bold yellow on #0f62fe")
                    else:
                        text.append(f"● {rg.name}", style="bold green")
                else:
                    text.append(f"  {rg.name}", style="dim white")
                if idx < len(self.resource_groups) - 1:
                    text.append("\n")

            rg_list.update(text)

        except Exception as e:
            ic(f"Error updating resource group display: {e}")

    # --- Region methods ---

    def set_regions(self, regions: List[Region], selected: Optional[Region] = None) -> None:
        """Set available regions"""
        self.regions = regions
        if selected:
            self.selected_region = selected
            self._region_index = next(
                (i for i, r in enumerate(regions) if r.name == selected.name), 0
            )
        elif regions:
            self.selected_region = regions[0]
            self._region_index = 0
        self._update_display()

    def select_region_by_number(self, number: int) -> None:
        """Select region by number key (0-9)"""
        if 0 <= number < len(self.regions):
            self._region_index = number
            self._select_region(self.regions[number])

    def select_next_region(self) -> None:
        """Select next region"""
        if not self.regions:
            return
        self._region_index = (self._region_index + 1) % len(self.regions)
        self._select_region(self.regions[self._region_index])

    def select_previous_region(self) -> None:
        """Select previous region"""
        if not self.regions:
            return
        self._region_index = (self._region_index - 1) % len(self.regions)
        self._select_region(self.regions[self._region_index])

    def _select_region(self, region: Region) -> None:
        """Select a region and emit change message"""
        if self.selected_region != region:
            self.selected_region = region
            self._update_display()
            self.post_message(self.RegionChanged(region))

    # --- Resource Group methods ---

    def set_resource_groups(self, resource_groups: List[ResourceGroup],
                           selected: Optional[ResourceGroup] = None) -> None:
        """Set available resource groups"""
        self.resource_groups = resource_groups
        if selected:
            self.selected_resource_group = selected
            self._resource_group_index = next(
                (i for i, rg in enumerate(resource_groups) if rg.id == selected.id), 0
            )
        elif resource_groups:
            self.selected_resource_group = resource_groups[0]
            self._resource_group_index = 0
        self._update_display()

    def set_resource_group(self, resource_group: Optional[ResourceGroup]) -> None:
        """Set the selected resource group"""
        self.selected_resource_group = resource_group
        if resource_group and self.resource_groups:
            self._resource_group_index = next(
                (i for i, rg in enumerate(self.resource_groups) if rg.id == resource_group.id), 0
            )
        self._update_display()

    def select_next_resource_group(self) -> None:
        """Select next resource group"""
        if not self.resource_groups:
            return
        self._resource_group_index = (self._resource_group_index + 1) % len(self.resource_groups)
        new_rg = self.resource_groups[self._resource_group_index]
        self.selected_resource_group = new_rg
        self._update_display()
        self.post_message(self.ResourceGroupSelectionRequested())

    def select_previous_resource_group(self) -> None:
        """Select previous resource group"""
        if not self.resource_groups:
            return
        self._resource_group_index = (self._resource_group_index - 1) % len(self.resource_groups)
        new_rg = self.resource_groups[self._resource_group_index]
        self.selected_resource_group = new_rg
        self._update_display()
        self.post_message(self.ResourceGroupSelectionRequested())

    # --- Resource Type methods ---

    def select_resource_type_by_key(self, key: str) -> None:
        """Select resource type by keyboard shortcut (1-4)"""
        key_map = {
            "1": ResourceType.VPC,
            "2": ResourceType.IKS,
            "3": ResourceType.ROKS,
            "4": ResourceType.CODE_ENGINE,
        }
        if key in key_map:
            resource_type = key_map[key]
            self._resource_type_index = self._resource_types.index(resource_type)
            self._select_resource_type(resource_type)

    def _select_resource_type(self, resource_type: ResourceType) -> None:
        """Select a resource type and emit change message"""
        if self.selected_resource_type != resource_type:
            self.selected_resource_type = resource_type
            self._update_display()
            self.post_message(self.ResourceTypeChanged(resource_type))

    def set_resource_type_display(self, display_name: str) -> None:
        """Set the resource type display name"""
        self.resource_type_display = display_name
        self._update_display()

    # --- Focus methods ---

    def set_region_focused(self, focused: bool) -> None:
        """Set region focus state"""
        self._region_focused = focused
        self._resource_group_focused = False
        self._update_display()
        # CSS class for styling
        try:
            col = self.query_one("#region_column")
            if focused:
                col.add_class("focused")
            else:
                col.remove_class("focused")
        except:
            pass

    def set_resource_group_focused(self, focused: bool) -> None:
        """Set resource group focus state"""
        self._resource_group_focused = focused
        self._region_focused = False
        if focused and self.resource_groups and self.selected_resource_group:
            self._resource_group_index = next(
                (i for i, rg in enumerate(self.resource_groups)
                 if rg.id == self.selected_resource_group.id), 0
            )
        self._update_display()
        # CSS class for styling
        try:
            col = self.query_one("#resource_group_column")
            if focused:
                col.add_class("focused")
            else:
                col.remove_class("focused")
        except:
            pass

    def clear_focus(self) -> None:
        """Clear all focus"""
        self._region_focused = False
        self._resource_group_focused = False
        self._update_display()
        try:
            self.query_one("#region_column").remove_class("focused")
            self.query_one("#resource_group_column").remove_class("focused")
        except:
            pass

    # --- Info display ---

    def update_instance_counts(self, total: int, running: int, stopped: int) -> None:
        """Update instance count display"""
        self.total_instances = total
        self.running_instances = running
        self.stopped_instances = stopped

    @property
    def region_count(self) -> int:
        """Get number of available regions"""
        return len(self.regions)

    @property
    def is_region_focused(self) -> bool:
        """Check if region selector is focused"""
        return self._region_focused

    @property
    def is_resource_group_focused(self) -> bool:
        """Check if resource group selector is focused"""
        return self._resource_group_focused
