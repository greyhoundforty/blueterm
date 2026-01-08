"""Instance table widget using Textual DataTable"""
from typing import List, Optional

from rich.text import Text
from textual.widgets import DataTable
from textual.coordinate import Coordinate

from ..api.models import Instance


class InstanceTable(DataTable):
    """
    DataTable widget displaying VPC instances with sortable columns.

    Columns: Name, Status, Zone, VPC, Profile, IP Address

    Keyboard Navigation:
        j/k or ↑/↓: Navigate rows
        Enter: View instance details
    """

    COLUMN_KEYS = ["name", "status", "zone", "vpc", "profile", "ip"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.instances: List[Instance] = []
        self.cursor_type = "row"
        self.zebra_stripes = True
        self._setup_columns()

    def _setup_columns(self) -> None:
        """Initialize table columns"""
        self.add_column("Name", key="name")
        self.add_column("Status", key="status")
        self.add_column("Zone", key="zone")
        self.add_column("VPC", key="vpc")
        self.add_column("Profile", key="profile")
        self.add_column("IP Address", key="ip")

    def update_instances(self, instances: List[Instance]) -> None:
        """
        Update table with new instance list

        Args:
            instances: List of Instance objects to display
        """
        self.instances = instances
        self.clear()

        if not instances:
            # Show empty state message
            self.add_row(
                Text("No instances found", style="dim italic"),
                "", "", "", "", "",
                key="empty"
            )
            return

        for instance in instances:
            # Style status with color and symbol
            status_text = Text(
                f"{instance.status.symbol} {instance.status.value}",
                style=instance.status.color
            )

            self.add_row(
                instance.name,
                status_text,
                instance.zone,
                instance.vpc_name,
                instance.profile,
                instance.primary_ip or "N/A",
                key=instance.id
            )

    def get_selected_instance(self) -> Optional[Instance]:
        """
        Get the currently selected instance

        Returns:
            Instance object if a row is selected, None otherwise
        """
        if not self.instances:
            return None

        if self.cursor_row < 0 or self.cursor_row >= len(self.instances):
            return None

        return self.instances[self.cursor_row]

    def get_instance_by_id(self, instance_id: str) -> Optional[Instance]:
        """
        Get instance by ID

        Args:
            instance_id: Instance UUID

        Returns:
            Instance object if found, None otherwise
        """
        return next((inst for inst in self.instances if inst.id == instance_id), None)

    def sort_by_column(self, column: str, reverse: bool = False) -> None:
        """
        Sort instances by specified column

        Args:
            column: Column key to sort by
            reverse: Sort in descending order if True
        """
        if column not in self.COLUMN_KEYS:
            return

        key_map = {
            "name": lambda i: i.name.lower(),
            "status": lambda i: i.status.value,
            "zone": lambda i: i.zone,
            "vpc": lambda i: i.vpc_name.lower(),
            "profile": lambda i: i.profile,
            "ip": lambda i: i.primary_ip or ""
        }

        self.instances.sort(key=key_map[column], reverse=reverse)
        self.update_instances(self.instances)

    def filter_instances(self, query: str) -> None:
        """
        Filter displayed instances by search query

        Args:
            query: Search string to filter by (matches name or status)
        """
        if not query:
            return

        query_lower = query.lower()
        filtered = [
            inst for inst in self.instances
            if query_lower in inst.name.lower() or query_lower in inst.status.value.lower()
        ]
        self.update_instances(filtered)

    @property
    def instance_count(self) -> int:
        """Get number of instances in table"""
        return len(self.instances)

    @property
    def has_instances(self) -> bool:
        """Check if table has any instances"""
        return len(self.instances) > 0
