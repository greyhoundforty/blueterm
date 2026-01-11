"""Region selector TAWS-style layout widget"""
from typing import List, Optional

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static, Label, Button
from rich.text import Text
from icecream import ic

from ..api.models import Region, ResourceGroup

class RegionSelector(Widget):
    """
    TAWS-style region selector with numbered regions.
    Shows: Profile | Region: <current> | Resource Group: <current> | Resource: VPC Instances
    Then lists: <0> region1  <1> region2  etc.

    Keyboard Navigation:
        0-9: Jump to region by number
        h/l or ←/→: Switch between regions
    """

    selected_region: reactive[Optional[Region]] = reactive(None)
    selected_resource_group: reactive[Optional[ResourceGroup]] = reactive(None)

    class RegionChanged(Message):
        """Message emitted when region selection changes"""
        def __init__(self, region: Region) -> None:
            self.region = region
            super().__init__()

    class ResourceGroupSelectionRequested(Message):
        """Message emitted when user requests to change resource group"""
        pass

    class ThemeCycleRequested(Message):
        """Message emitted when user requests to cycle theme"""
        pass

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.regions: List[Region] = []
        self._selected_index: int = 0
        self.total_instances: int = 0
        self.running_instances: int = 0
        self.stopped_instances: int = 0
        self.resource_groups: List[ResourceGroup] = []
        self.resource_type_display: str = "VPC Instances"
        self.current_theme: str = "ibm-carbon"

    def compose(self) -> ComposeResult:
        """Compose TAWS-style layout"""
        with Vertical(id="region_panel"):
            # Top info bar - simplified (region, resource type, counts only)
            with Horizontal(id="region_info_bar"):
                yield Label("Profile: ", id="profile_label")
                yield Label("ibmcloud", id="profile_value")
                yield Label("  Region: ", id="region_label")
                yield Label("", id="current_region")
                yield Label("  Resource Group: ", id="rg_label_inline")
                yield Label("N/A", id="current_resource_group_inline")
                yield Button("Change", variant="primary", id="change_rg_button_inline")
                yield Label("  Theme: ", id="theme_label_inline")
                yield Label("ibm-carbon", id="current_theme_inline")
                yield Button("Change", variant="primary", id="change_theme_button_inline")
                yield Label("  Resource: ", id="resource_label")
                yield Label("VPC Instances", id="resource_value")
                yield Label("  Instances: ", id="instances_label")
                yield Label("", id="instances_count")

            # Region list with numbers
            yield Static("", id="region_list")

    def set_regions(self, regions: List[Region], selected: Optional[Region] = None) -> None:
        """
        Set available regions and optionally select one

        Args:
            regions: List of Region objects
            selected: Initial region to select (defaults to first region)
        """
        self.regions = regions
        if selected:
            self.selected_region = selected
            self._selected_index = next(
                (i for i, r in enumerate(regions) if r.name == selected.name),
                0
            )
        elif regions:
            self.selected_region = regions[0]
            self._selected_index = 0

        self._update_display()

    def _update_display(self) -> None:
        """Update the region list display"""
        # Update current region label (only if regions are loaded)
        if self.regions:
            try:
                current_region_label = self.query_one("#current_region", Label)
                if self.selected_region:
                    current_region_label.update(Text(self.selected_region.name, style="bold green"))
            except:
                pass

        # Update resource group display
        try:
            current_rg_label = self.query_one("#current_resource_group_inline", Label)
            if self.selected_resource_group:
                current_rg_label.update(Text(self.selected_resource_group.name, style="bold green"))
            else:
                current_rg_label.update("N/A")
        except:
            pass

        # Update theme display
        try:
            current_theme_label = self.query_one("#current_theme_inline", Label)
            current_theme_label.update(Text(self.current_theme, style="bold cyan"))
        except:
            pass

        # Update instance counts
        try:
            instances_count_label = self.query_one("#instances_count", Label)
            count_text = f"{self.total_instances} (●{self.running_instances} ○{self.stopped_instances})"
            instances_count_label.update(count_text)
        except:
            pass

        # Update resource type display
        try:
            resource_value_label = self.query_one("#resource_value", Label)
            resource_value_label.update(Text(self.resource_type_display, style="bold white"))
        except:
            pass

        # Build region list text (TAWS style - vertical columns) - only if regions are loaded
        if not self.regions:
            return

        region_list_static = self.query_one("#region_list", Static)
        region_text = Text()

        # Display regions in vertical columns (5 rows, then next column)
        # Calculate layout: 5 rows max, then new column
        # Support up to 20 regions (0-9 and a-z for extended support)
        num_regions = len(self.regions)
        rows = 5
        cols = (num_regions + rows - 1) // rows  # Ceiling division

        for row in range(rows):
            row_parts = []
            for col in range(cols):
                idx = col * rows + row
                if idx >= num_regions:
                    break

                region = self.regions[idx]

                # Format: <0> region-name (only show number for first 10 regions)
                num_style = "bold cyan" if idx == self._selected_index else "dim"
                name_style = "bold green" if idx == self._selected_index else "white"

                part = Text()
                # Only show number prefix for regions 0-9 (accessible via number keys)
                if idx < 10:
                    part.append(f"<{idx}>", style=num_style)
                    part.append(" ")
                else:
                    # No number prefix for regions beyond 9 (use h/l navigation)
                    part.append("    ")  # Spacing to align with numbered regions
                part.append(region.name, style=name_style)
                row_parts.append(part)

            # Add row to main text with proper spacing
            for i, part in enumerate(row_parts):
                if i > 0:
                    region_text.append("    ")  # Column spacing
                region_text.append(part)

            if row < rows - 1:  # Don't add newline after last row
                region_text.append("\n")

        region_list_static.update(region_text)

    def select_by_number(self, number: int) -> None:
        """Select region by number key (0-9)"""
        if 0 <= number < len(self.regions):
            self._selected_index = number
            self._select_region(self.regions[number])

    def select_next(self) -> None:
        """Select next region (right/l key)"""
        if not self.regions:
            return

        self._selected_index = (self._selected_index + 1) % len(self.regions)
        self._select_region(self.regions[self._selected_index])

    def select_previous(self) -> None:
        """Select previous region (left/h key)"""
        if not self.regions:
            return

        self._selected_index = (self._selected_index - 1) % len(self.regions)
        self._select_region(self.regions[self._selected_index])

    def _select_region(self, region: Region) -> None:
        """
        Select a region and emit change message

        Args:
            region: Region to select
        """
        if self.selected_region != region:
            self.selected_region = region
            self._update_display()
            self.post_message(self.RegionChanged(region))

    def watch_selected_region(self, old_region: Optional[Region], new_region: Optional[Region]) -> None:
        """React to selected region changes (Textual reactive property)"""
        if new_region:
            self._update_display()

    def watch_selected_resource_group(self, old_rg: Optional[ResourceGroup], new_rg: Optional[ResourceGroup]) -> None:
        """React to selected resource group changes (Textual reactive property)"""
        if new_rg:
            self._update_display()

    def set_resource_groups(self, resource_groups: List[ResourceGroup], selected: Optional[ResourceGroup] = None) -> None:
        """
        Set available resource groups and optionally select one

        Args:
            resource_groups: List of ResourceGroup objects
            selected: Initial resource group to select (defaults to first)
        """
        ic(f"set_resource_groups called with {len(resource_groups)} groups, selected={selected}")
        self.resource_groups = resource_groups
        if selected:
            self.selected_resource_group = selected
            ic(f"Using provided selected resource group: {selected.name}")
        elif resource_groups:
            self.selected_resource_group = resource_groups[0]
            ic(f"Using first resource group: {resource_groups[0].name}")
        else:
            self.selected_resource_group = None
            ic("No resource groups available, setting to None")
        ic(f"About to call _update_display, selected_resource_group={self.selected_resource_group}")
        self._update_display()

    def set_resource_type_display(self, resource_type: str) -> None:
        """
        Set the resource type display text

        Args:
            resource_type: Resource type display string (e.g., "VPC Instances", "Code Engine Projects")
        """
        self.resource_type_display = resource_type
        self._update_display()

    def set_resource_group(self, resource_group: Optional[ResourceGroup]) -> None:
        """
        Set the selected resource group and update display

        Args:
            resource_group: ResourceGroup to select or None
        """
        self.selected_resource_group = resource_group
        self._update_display()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle Change button press for resource group and theme"""
        if event.button.id == "change_rg_button_inline":
            # Emit message to request resource group selection
            self.post_message(self.ResourceGroupSelectionRequested())
        elif event.button.id == "change_theme_button_inline":
            # Emit message to request theme cycle
            self.post_message(self.ThemeCycleRequested())

    def set_theme(self, theme_name: str) -> None:
        """
        Set the current theme name for display

        Args:
            theme_name: Theme name to display
        """
        self.current_theme = theme_name
        self._update_display()

    def update_instance_counts(self, total: int, running: int, stopped: int) -> None:
        """
        Update instance count display

        Args:
            total: Total number of instances
            running: Number of running instances
            stopped: Number of stopped instances
        """
        self.total_instances = total
        self.running_instances = running
        self.stopped_instances = stopped
        self._update_display()

    @property
    def region_count(self) -> int:
        """Get number of available regions"""
        return len(self.regions)
