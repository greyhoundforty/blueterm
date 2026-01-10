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

    VPC_COLUMN_KEYS = ["name", "status", "zone", "vpc", "profile", "ip"]
    IKS_COLUMN_KEYS = ["name", "region", "vpc", "workers", "pools", "version"]
    ROKS_COLUMN_KEYS = ["name", "region", "vpc", "workers", "pools", "version"]
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
        elif self.resource_type == ResourceType.IKS:
            self.add_column("Name", key="name")
            self.add_column("Region", key="region")
            self.add_column("VPC", key="vpc")
            self.add_column("Workers", key="workers")
            self.add_column("Pools", key="pools")
            self.add_column("Version", key="version")
        elif self.resource_type == ResourceType.ROKS:
            self.add_column("Name", key="name")
            self.add_column("Region", key="region")
            self.add_column("VPC", key="vpc")
            self.add_column("Workers", key="workers")
            self.add_column("Pools", key="pools")
            self.add_column("Version", key="version")
        else:  # VPC
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
            elif self.resource_type in (ResourceType.IKS, ResourceType.ROKS):
                # For IKS/ROKS clusters, show cluster-specific columns
                # Parse metadata from vpc_name (format: "IKS v1.28.5" or "OpenShift 4.14.8")
                # Parse metadata from profile (format: "3 workers" or "3 workers, 2 pools")
                workers_info = instance.profile.split(",")
                workers = workers_info[0].strip() if workers_info else "N/A"
                pools = workers_info[1].strip() if len(workers_info) > 1 else "1 pool"

                # Extract VPC from vpc_id (if available) or use placeholder
                vpc_display = instance.vpc_id if instance.vpc_id else "N/A"

                self.add_row(
                    instance.name,
                    instance.zone,  # Region
                    vpc_display,    # VPC
                    workers,        # Workers count
                    pools,          # Worker pools count
                    instance.vpc_name,  # Version (stored in vpc_name field)
                    key=instance.id
                )
            else:
                # For VPC, show standard instance columns
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
        # Build appropriate column keys based on resource type
        valid_keys = self.VPC_COLUMN_KEYS
        if self.resource_type == ResourceType.IKS:
            valid_keys = self.IKS_COLUMN_KEYS
        elif self.resource_type == ResourceType.ROKS:
            valid_keys = self.ROKS_COLUMN_KEYS
        elif self.resource_type == ResourceType.CODE_ENGINE:
            valid_keys = self.CODE_ENGINE_COLUMN_KEYS

        if column not in valid_keys:
            return

        # Common sort keys
        key_map = {
            "name": lambda i: i.name.lower(),
            "status": lambda i: i.status.value,
            "zone": lambda i: i.zone,
            "region": lambda i: i.zone,  # Region uses zone field
            "vpc": lambda i: i.vpc_name.lower(),
            "profile": lambda i: i.profile,
            "ip": lambda i: i.primary_ip or "",
            "workers": lambda i: i.profile.split()[0] if i.profile else "",
            "version": lambda i: i.vpc_name  # Version stored in vpc_name for clusters
        }

        if column in key_map:
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
