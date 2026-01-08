"""Region selector TAWS-style layout widget"""
from typing import List, Optional

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static, Label
from rich.text import Text

from ..api.models import Region


class RegionSelector(Widget):
    """
    TAWS-style region selector with numbered regions.
    Shows: Profile | Region: <current> | Resource: VPC Instances
    Then lists: <0> region1  <1> region2  etc.

    Keyboard Navigation:
        0-9: Jump to region by number
        h/l or ←/→: Switch between regions
    """

    selected_region: reactive[Optional[Region]] = reactive(None)

    class RegionChanged(Message):
        """Message emitted when region selection changes"""
        def __init__(self, region: Region) -> None:
            self.region = region
            super().__init__()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.regions: List[Region] = []
        self._selected_index: int = 0
        self.total_instances: int = 0
        self.running_instances: int = 0
        self.stopped_instances: int = 0

    def compose(self) -> ComposeResult:
        """Compose TAWS-style layout"""
        with Vertical(id="region_panel"):
            # Top info bar
            with Horizontal(id="region_info_bar"):
                yield Label("Profile: ", id="profile_label")
                yield Label("ibmcloud", id="profile_value")
                yield Label("  Region: ", id="region_label")
                yield Label("", id="current_region")
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
        if not self.regions:
            return

        # Update current region label
        try:
            current_region_label = self.query_one("#current_region", Label)
            if self.selected_region:
                current_region_label.update(self.selected_region.name)
        except:
            pass

        # Update instance counts
        try:
            instances_count_label = self.query_one("#instances_count", Label)
            count_text = f"{self.total_instances} (●{self.running_instances} ○{self.stopped_instances})"
            instances_count_label.update(count_text)
        except:
            pass

        # Build region list text (TAWS style - vertical columns)
        region_list_static = self.query_one("#region_list", Static)
        region_text = Text()

        # Display regions in vertical columns (5 rows, then next column)
        # Calculate layout: 5 rows max, then new column
        num_regions = min(len(self.regions), 10)  # Limit to 0-9
        rows = 5
        cols = (num_regions + rows - 1) // rows  # Ceiling division

        for row in range(rows):
            row_parts = []
            for col in range(cols):
                idx = col * rows + row
                if idx >= num_regions:
                    break

                region = self.regions[idx]

                # Format: <0> region-name
                num_style = "bold cyan" if idx == self._selected_index else "dim"
                name_style = "bold green" if idx == self._selected_index else "white"

                part = Text()
                part.append(f"<{idx}>", style=num_style)
                part.append(" ")
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
