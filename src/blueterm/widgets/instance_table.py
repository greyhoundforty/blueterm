"""Instance table widget using Textual DataTable"""
from typing import List, Optional
from enum import Enum

from rich.text import Text
from textual.widgets import DataTable
from textual.coordinate import Coordinate

from ..api.models import Instance


class ResourceType(Enum):
    """Resource type for table column configuration"""
    VPC = "vpc"
    IKS = "iks"
    ROKS = "roks"
    CODE_ENGINE = "code_engine"


class InstanceTable(DataTable):
    """
    DataTable widget displaying VPC instances with sortable columns.

    Columns: Name, Status, Zone, VPC, Profile, IP Address
    Code Engine Columns: Name, Apps, Jobs, Builds, Secrets

    Keyboard Navigation:
        j/k or ↑/↓: Navigate rows
        Enter: View instance details
    """

    COLUMN_KEYS = ["name", "status", "zone", "vpc", "profile", "ip"]
    CODE_ENGINE_COLUMN_KEYS = ["name", "apps", "jobs", "builds", "secrets"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.instances: List[Instance] = []
        self.cursor_type = "row"
        self.zebra_stripes = True
        self.resource_type: ResourceType = ResourceType.VPC
        self._setup_columns()

    def _setup_columns(self) -> None:
        """Initialize table columns based on resource type"""
        self.clear(columns=True)
        
        if self.resource_type == ResourceType.CODE_ENGINE:
            self.add_column("Name", key="name")
            self.add_column("Apps", key="apps")
            self.add_column("Jobs", key="jobs")
            self.add_column("Builds", key="builds")
            self.add_column("Secrets", key="secrets")
        else:
            self.add_column("Name", key="name")
            self.add_column("Status", key="status")
            self.add_column("Zone", key="zone")
            self.add_column("VPC", key="vpc")
            self.add_column("Profile", key="profile")
            self.add_column("IP Address", key="ip")

    def set_resource_type(self, resource_type: ResourceType) -> None:
        """
        Set the resource type and update columns accordingly
        
        Args:
            resource_type: The resource type to display
        """
        if self.resource_type != resource_type:
            self.resource_type = resource_type
            self._setup_columns()

    def update_instances(self, instances: List[Instance], project_counts: Optional[dict] = None) -> None:
        """
        Update table with new instance list

        Args:
            instances: List of Instance objects to display
            project_counts: Optional dict mapping project IDs to counts (for Code Engine)
                           Format: {project_id: {"apps": int, "jobs": int, "builds": int, "secrets": int}}
        """
        self.instances = instances
        self.clear()

        if not instances:
            # Show empty state message
            if self.resource_type == ResourceType.CODE_ENGINE:
                self.add_row(
                    Text("No projects found", style="dim italic"),
                    "", "", "", "",
                    key="empty"
                )
            else:
                self.add_row(
                    Text("No instances found", style="dim italic"),
                    "", "", "", "", "",
                    key="empty"
                )
            return

        for instance in instances:
            if self.resource_type == ResourceType.CODE_ENGINE:
                # For Code Engine, show project name and counts
                counts = project_counts.get(instance.id, {}) if project_counts else {}
                apps_count = counts.get("apps", 0)
                jobs_count = counts.get("jobs", 0)
                builds_count = counts.get("builds", 0)
                secrets_count = counts.get("secrets", 0)
                
                self.add_row(
                    instance.name,
                    Text(str(apps_count), style="cyan"),
                    Text(str(jobs_count), style="yellow"),
                    Text(str(builds_count), style="green"),
                    Text(str(secrets_count), style="magenta"),
                    key=instance.id
                )
            else:
                # For VPC/IKS/ROKS, show standard columns
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
