"""Data models for IBM Cloud VPC resources"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class InstanceStatus(Enum):
    """VPC instance status values with color mappings for display"""
    RUNNING = "running"
    STOPPED = "stopped"
    STARTING = "starting"
    STOPPING = "stopping"
    PENDING = "pending"
    FAILED = "failed"
    DELETING = "deleting"
    RESTARTING = "restarting"

    @property
    def color(self) -> str:
        """Return Rich color code for status display"""
        color_map = {
            self.RUNNING: "green",
            self.STOPPED: "red",
            self.STARTING: "yellow",
            self.STOPPING: "yellow",
            self.PENDING: "blue",
            self.FAILED: "red bold",
            self.DELETING: "magenta",
            self.RESTARTING: "yellow"
        }
        return color_map.get(self, "white")

    @property
    def symbol(self) -> str:
        """Return status symbol for compact display"""
        symbol_map = {
            self.RUNNING: "●",
            self.STOPPED: "○",
            self.STARTING: "◐",
            self.STOPPING: "◑",
            self.PENDING: "◎",
            self.FAILED: "✗",
            self.DELETING: "⊗",
            self.RESTARTING: "↻"
        }
        return symbol_map.get(self, "?")


@dataclass
class Region:
    """IBM Cloud VPC Region"""
    name: str
    endpoint: str
    status: str

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Region(name='{self.name}', status='{self.status}')"


@dataclass
class Instance:
    """IBM Cloud VPC Instance"""
    id: str
    name: str
    status: InstanceStatus
    zone: str
    vpc_name: str
    vpc_id: str
    profile: str
    primary_ip: Optional[str]
    created_at: str
    crn: str

    @property
    def short_id(self) -> str:
        """Return shortened ID for display (first 8 characters)"""
        return self.id[:8] if self.id else ""

    @property
    def can_start(self) -> bool:
        """Check if instance can be started"""
        return self.status == InstanceStatus.STOPPED

    @property
    def can_stop(self) -> bool:
        """Check if instance can be stopped"""
        return self.status == InstanceStatus.RUNNING

    @property
    def can_reboot(self) -> bool:
        """Check if instance can be rebooted"""
        return self.status == InstanceStatus.RUNNING

    @property
    def status_display(self) -> str:
        """Return formatted status string with symbol"""
        return f"{self.status.symbol} {self.status.value}"

    def __str__(self) -> str:
        return f"{self.name} ({self.status.value})"

    def __repr__(self) -> str:
        return f"Instance(id='{self.short_id}...', name='{self.name}', status={self.status.value})"
