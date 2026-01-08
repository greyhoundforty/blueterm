"""Info bar widget for displaying region, resource group, and time"""
from datetime import datetime
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label
from rich.text import Text

from ..api.models import Region, ResourceGroup


class InfoBar(Widget):
    """
    Info bar widget displayed in top-right corner.

    Shows:
        Region: <region-name>  |  Resource Group: <rg-name>  |  <date-time>
    """

    current_region: reactive[Optional[str]] = reactive(None)
    current_resource_group: reactive[Optional[str]] = reactive(None)
    current_time: reactive[str] = reactive("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        """Compose info bar layout"""
        with Horizontal(id="info_bar_container"):
            yield Label("Region: ", id="info_region_label")
            yield Label("", id="info_region_value")
            yield Label("  |  Resource Group: ", id="info_rg_label")
            yield Label("", id="info_rg_value")
            yield Label("  |  ", id="info_separator")
            yield Label("", id="info_time_value")

    def set_region(self, region: Optional[Region]) -> None:
        """
        Set the current region

        Args:
            region: Region object or None
        """
        if region:
            self.current_region = region.name
        else:
            self.current_region = "N/A"
        self._update_display()

    def set_resource_group(self, resource_group: Optional[ResourceGroup]) -> None:
        """
        Set the current resource group

        Args:
            resource_group: ResourceGroup object or None
        """
        if resource_group:
            self.current_resource_group = resource_group.name
        else:
            self.current_resource_group = "N/A"
        self._update_display()

    def update_time(self) -> None:
        """Update the current time display"""
        now = datetime.now()
        self.current_time = now.strftime("%Y-%m-%d %H:%M:%S")
        self._update_display()

    def _update_display(self) -> None:
        """Update all display values"""
        try:
            # Update region
            region_value = self.query_one("#info_region_value", Label)
            region_value.update(Text(self.current_region or "N/A", style="bold cyan"))

            # Update resource group
            rg_value = self.query_one("#info_rg_value", Label)
            rg_value.update(Text(self.current_resource_group or "N/A", style="bold green"))

            # Update time
            time_value = self.query_one("#info_time_value", Label)
            time_value.update(Text(self.current_time, style="bold yellow"))
        except:
            # Widgets not yet mounted
            pass

    def watch_current_region(self, old_value: Optional[str], new_value: Optional[str]) -> None:
        """React to region changes"""
        self._update_display()

    def watch_current_resource_group(self, old_value: Optional[str], new_value: Optional[str]) -> None:
        """React to resource group changes"""
        self._update_display()

    def watch_current_time(self, old_value: str, new_value: str) -> None:
        """React to time changes"""
        self._update_display()
