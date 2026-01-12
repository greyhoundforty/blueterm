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
        self._region_focused: bool = False
        self._resource_group_focused: bool = False
        self._resource_group_index: int = 0

    def compose(self) -> ComposeResult:
        """Compose btop-style layout with distinct sections"""
        with Vertical(id="region_panel"):
            # Top info bar - simplified (resource type, counts only)
            with Horizontal(id="region_info_bar"):
                yield Label("Resource: ", id="resource_label")
                yield Label("VPC Instances", id="resource_value")
                yield Label("  Instances: ", id="instances_label")
                yield Label("", id="instances_count")
            
            # Btop-style horizontal sections
            with Horizontal(id="nav_sections"):
                # Regions section
                with Vertical(id="regions_section"):
                    yield Label("", id="regions_label")
                    yield Static("", id="regions_list")
                
                # Resource Group section
                with Vertical(id="resource_group_section"):
                    yield Label("", id="rg_section_label")
                    yield Static("", id="resource_group_list")
    
    def on_mount(self) -> None:
        """Called when widget is mounted - ensure display is updated"""
        ic("RegionSelector mounted, calling _update_display")
        # Use call_after_refresh to ensure widgets are fully ready
        self.call_after_refresh(self._update_display)

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
        """Update the display with btop-style sections"""
        ic(f"_update_display called: regions={len(self.regions)}, resource_groups={len(self.resource_groups)}")
        ic(f"Widget mounted: {self.is_mounted}")
        
        # Check if widget is mounted before trying to update
        if not self.is_mounted:
            ic("Widget not mounted yet, skipping display update")
            return
        
        # Update instance counts
        try:
            instances_count_label = self.query_one("#instances_count", Label)
            count_text = f"{self.total_instances} (●{self.running_instances} ○{self.stopped_instances})"
            instances_count_label.update(count_text)
            ic(f"Updated instance counts: {count_text}")
        except Exception as e:
            import traceback
            ic(f"Error updating instance counts: {e}")
            ic(f"Traceback: {traceback.format_exc()}")

        # Update resource type display
        try:
            resource_value_label = self.query_one("#resource_value", Label)
            resource_value_label.update(Text(self.resource_type_display, style="bold white"))
            ic(f"Updated resource type: {self.resource_type_display}")
        except Exception as e:
            ic(f"Error updating resource type: {e}")

        # Update regions section label (show focus indicator and keyboard shortcut)
        try:
            regions_label = self.query_one("#regions_label", Label)
            if self._region_focused:
                # When focused: show >> [R]egion << with R highlighted
                label_text = Text()
                label_text.append(">> ", style="bold yellow on #0f62fe")
                label_text.append("[", style="bold yellow on #0f62fe")
                label_text.append("R", style="bold white on #0f62fe")
                label_text.append("]", style="bold yellow on #0f62fe")
                label_text.append("egion <<", style="bold yellow on #0f62fe")
                regions_label.update(label_text)
            else:
                # When not focused: show [R]egion with R highlighted
                label_text = Text()
                label_text.append("[", style="bold cyan")
                label_text.append("R", style="bold white")
                label_text.append("]", style="bold cyan")
                label_text.append("egion", style="bold cyan")
                regions_label.update(label_text)
            ic(f"Updated regions label, focused={self._region_focused}")
        except Exception as e:
            ic(f"Error updating regions label: {e}")

        # Update regions list - horizontal spanning layout
        try:
            regions_list = self.query_one("#regions_list", Static)
            if not self.regions:
                regions_list.update("No regions")
                ic("No regions to display")
            else:
                region_text = Text()
                # Show regions horizontally, spanning the area
                for idx, region in enumerate(self.regions):
                    if idx == self._selected_index:
                        if self._region_focused:
                            region_text.append(f" {region.name} ", style="bold yellow on #0f62fe")
                        else:
                            region_text.append(f" {region.name} ", style="bold green on #262626")
                    else:
                        region_text.append(f" {region.name} ", style="dim white")
                    # Add separator between regions (except last)
                    if idx < len(self.regions) - 1:
                        region_text.append("│", style="dim")
                
                # Update and force refresh
                regions_list.update(region_text)
                regions_list.display = True
                regions_list.refresh(layout=True)
                ic(f"Updated regions list: {len(self.regions)} regions, selected_index={self._selected_index}")
                ic(f"Region names: {[r.name for r in self.regions]}")
                ic(f"Region text content: {region_text.plain}")
                ic(f"Regions list widget visible: {regions_list.display}, mounted: {regions_list.is_mounted}")
        except Exception as e:
            import traceback
            ic(f"Error updating regions list: {e}")
            ic(f"Traceback: {traceback.format_exc()}")

        # Update resource group section label (show focus indicator and keyboard shortcut)
        try:
            rg_section_label = self.query_one("#rg_section_label", Label)
            if self._resource_group_focused:
                # When focused: show >> [G]roup << with G highlighted
                label_text = Text()
                label_text.append(">> ", style="bold yellow on #0f62fe")
                label_text.append("[", style="bold yellow on #0f62fe")
                label_text.append("G", style="bold white on #0f62fe")
                label_text.append("]", style="bold yellow on #0f62fe")
                label_text.append("roup <<", style="bold yellow on #0f62fe")
                rg_section_label.update(label_text)
            else:
                # When not focused: show [G]roup with G highlighted
                label_text = Text()
                label_text.append("[", style="bold cyan")
                label_text.append("G", style="bold white")
                label_text.append("]", style="bold cyan")
                label_text.append("roup", style="bold cyan")
                rg_section_label.update(label_text)
            ic(f"Updated resource group label, focused={self._resource_group_focused}")
        except Exception as e:
            ic(f"Error updating resource group label: {e}")

        # Update resource group list - vertical list showing all groups
        try:
            rg_list = self.query_one("#resource_group_list", Static)
            if not self.resource_groups:
                rg_list.update("No resource groups")
                ic("No resource groups to display")
            else:
                rg_text = Text()
                # Show all resource groups in a vertical list
                for idx, rg in enumerate(self.resource_groups):
                    is_selected = (rg.id == self.selected_resource_group.id) if self.selected_resource_group else False
                    if is_selected:
                        if self._resource_group_focused:
                            rg_text.append(f"  {rg.name}", style="bold yellow on #0f62fe")
                        else:
                            rg_text.append(f"  {rg.name}", style="bold green on #262626")
                    else:
                        rg_text.append(f"  {rg.name}", style="dim white")
                    if idx < len(self.resource_groups) - 1:
                        rg_text.append("\n")
                # Update and force refresh
                rg_list.update(rg_text)
                rg_list.display = True
                rg_list.refresh(layout=True)
                ic(f"Updated resource group list: {len(self.resource_groups)} groups, selected={self.selected_resource_group.name if self.selected_resource_group else None}")
                ic(f"Resource group names: {[rg.name for rg in self.resource_groups]}")
                ic(f"Resource group text content: {rg_text.plain}")
                ic(f"Resource group list widget visible: {rg_list.display}, mounted: {rg_list.is_mounted}")
        except Exception as e:
            import traceback
            ic(f"Error updating resource group list: {e}")
            ic(f"Traceback: {traceback.format_exc()}")

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
            self._resource_group_index = next(
                (i for i, rg in enumerate(resource_groups) if rg.id == selected.id),
                0
            )
            ic(f"Using provided selected resource group: {selected.name}")
        elif resource_groups:
            self.selected_resource_group = resource_groups[0]
            self._resource_group_index = 0
            ic(f"Using first resource group: {resource_groups[0].name}")
        else:
            self.selected_resource_group = None
            self._resource_group_index = 0
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
        """Handle button press events"""
        # Buttons removed in new design, but keep for compatibility
        pass

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
    
    def set_focused(self, focused: bool) -> None:
        """
        Set region selector focus state
        
        Args:
            focused: True to focus region selector
        """
        self._region_focused = focused
        self._resource_group_focused = False
        self._update_display()
        # Add/remove CSS class for styling
        try:
            regions_section = self.query_one("#regions_section")
            if focused:
                regions_section.add_class("focused")
            else:
                regions_section.remove_class("focused")
        except:
            pass
    
    def set_resource_group_focused(self, focused: bool) -> None:
        """
        Set resource group selector focus state
        
        Args:
            focused: True to focus resource group selector
        """
        self._resource_group_focused = focused
        self._region_focused = False
        # Initialize resource group index if needed
        if focused and self.resource_groups and self.selected_resource_group:
            self._resource_group_index = next(
                (i for i, rg in enumerate(self.resource_groups) if rg.id == self.selected_resource_group.id),
                0
            )
        self._update_display()
        # Add/remove CSS class for styling
        try:
            rg_section = self.query_one("#resource_group_section")
            if focused:
                rg_section.add_class("focused")
            else:
                rg_section.remove_class("focused")
        except:
            pass
    
    def select_next_resource_group(self) -> None:
        """Select next resource group (right/l key when focused)"""
        if not self.resource_groups:
            return
        self._resource_group_index = (self._resource_group_index + 1) % len(self.resource_groups)
        new_rg = self.resource_groups[self._resource_group_index]
        self.selected_resource_group = new_rg
        self._update_display()
        self.post_message(self.ResourceGroupSelectionRequested())
    
    def select_previous_resource_group(self) -> None:
        """Select previous resource group (left/h key when focused)"""
        if not self.resource_groups:
            return
        self._resource_group_index = (self._resource_group_index - 1) % len(self.resource_groups)
        new_rg = self.resource_groups[self._resource_group_index]
        self.selected_resource_group = new_rg
        self._update_display()
        self.post_message(self.ResourceGroupSelectionRequested())
    
    def _select_resource_group(self, resource_group: ResourceGroup) -> None:
        """
        Select a resource group and emit change message
        
        Args:
            resource_group: ResourceGroup to select
        """
        if self.selected_resource_group != resource_group:
            self.selected_resource_group = resource_group
            self._update_display()
            # Emit ResourceGroupSelectionRequested to trigger actual change in app
            self.post_message(self.ResourceGroupSelectionRequested())

    @property
    def region_count(self) -> int:
        """Get number of available regions"""
        return len(self.regions)
