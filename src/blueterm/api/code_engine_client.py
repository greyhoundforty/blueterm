"""IBM Cloud Code Engine API Client"""
from typing import List, Optional
from datetime import datetime
import requests

from .models import Region, Instance, InstanceStatus
from .exceptions import AuthenticationError


class CodeEngineClient:
    """
    Client for IBM Cloud Code Engine v2 API.

    Manages Code Engine projects, applications, jobs, and functions.
    """

    def __init__(self, api_key: str):
        """
        Initialize Code Engine client with IBM Cloud API key

        Args:
            api_key: IBM Cloud API key for authentication

        Raises:
            AuthenticationError: If authentication fails
        """
        self.api_key = api_key
        self._current_region: Optional[str] = None
        self._resource_group_id: Optional[str] = None
        self._iam_token: str = None

    def _get_iam_token(self) -> str:
        """
        Get IAM access token from IBM Cloud

        Returns:
            IAM access token

        Raises:
            AuthenticationError: If token retrieval fails
        """
        if self._iam_token:
            return self._iam_token

        try:
            response = requests.post(
                "https://iam.cloud.ibm.com/identity/token",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                    "apikey": self.api_key
                }
            )
            response.raise_for_status()
            self._iam_token = response.json()["access_token"]
            return self._iam_token
        except Exception as e:
            raise AuthenticationError(f"Failed to get IAM token: {e}")

    async def list_regions(self) -> List[Region]:
        """
        List available Code Engine regions

        Returns:
            List of Region objects
        """
        # Code Engine supported regions
        return [
            Region(name="us-south", endpoint="https://api.us-south.codeengine.cloud.ibm.com", status="available"),
            Region(name="us-east", endpoint="https://api.us-east.codeengine.cloud.ibm.com", status="available"),
            Region(name="eu-gb", endpoint="https://api.eu-gb.codeengine.cloud.ibm.com", status="available"),
            Region(name="eu-de", endpoint="https://api.eu-de.codeengine.cloud.ibm.com", status="available"),
            Region(name="jp-tok", endpoint="https://api.jp-tok.codeengine.cloud.ibm.com", status="available"),
            Region(name="au-syd", endpoint="https://api.au-syd.codeengine.cloud.ibm.com", status="available"),
        ]

    def set_region(self, region_name: str) -> None:
        """
        Set the active region for API calls

        Args:
            region_name: Region identifier (e.g., 'us-south', 'eu-gb')
        """
        self._current_region = region_name

    def set_resource_group(self, resource_group_id: str) -> None:
        """
        Set the resource group ID for API calls

        Args:
            resource_group_id: Resource group ID
        """
        self._resource_group_id = resource_group_id

    async def list_projects(self, resource_group_id: Optional[str] = None) -> List[dict]:
        """
        List Code Engine projects in a resource group

        Args:
            resource_group_id: Optional resource group ID (uses set resource group if not provided)

        Returns:
            List of project dictionaries
        """
        if not resource_group_id:
            resource_group_id = self._resource_group_id

        if not resource_group_id:
            # Return empty list if no resource group is set
            return []

        try:
            token = self._get_iam_token()
            region = self._current_region or "us-south"

            response = requests.get(
                f"https://api.{region}.codeengine.cloud.ibm.com/v2/projects",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                params={
                    "resource_group_id": resource_group_id,
                    "limit": 100
                }
            )
            response.raise_for_status()

            projects = response.json().get("projects", [])
            return projects
        except Exception as e:
            # Return empty list on error (graceful degradation)
            print(f"Error fetching Code Engine projects: {e}")
            return []

    async def list_instances(self, region: Optional[str] = None) -> List[Instance]:
        """
        List Code Engine projects as Instance objects

        Args:
            region: Optional region to list projects from

        Returns:
            List of Instance objects representing Code Engine projects
        """
        if region and region != self._current_region:
            self.set_region(region)

        projects = await self.list_projects()

        instances = []
        for project in projects:
            # Convert Code Engine project to Instance object for display
            status_map = {
                "active": InstanceStatus.RUNNING,
                "inactive": InstanceStatus.STOPPED,
                "creating": InstanceStatus.STARTING,
                "deleting": InstanceStatus.DELETING,
                "failed": InstanceStatus.FAILED,
            }

            instance = Instance(
                id=project.get("id", ""),
                name=project.get("name", ""),
                status=status_map.get(project.get("status", "active"), InstanceStatus.PENDING),
                zone=self._current_region or "us-south",
                vpc_name="Code Engine",  # Use service name
                vpc_id=project.get("resource_group_id", ""),
                profile="Project",  # Resource type
                primary_ip=None,  # Not applicable for Code Engine
                created_at=project.get("created_at", datetime.now().isoformat()),
                crn=project.get("crn", "")
            )
            instances.append(instance)

        return instances

    async def start_instance(self, instance_id: str) -> None:
        """Code Engine projects don't have start/stop lifecycle"""
        pass

    async def stop_instance(self, instance_id: str) -> None:
        """Code Engine projects don't have start/stop lifecycle"""
        pass

    async def reboot_instance(self, instance_id: str) -> None:
        """Code Engine projects don't have reboot functionality"""
        pass
