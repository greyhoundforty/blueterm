"""IBM Cloud VPC API Client Wrapper"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ibm_vpc import VpcV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core import ApiException

from .models import Region, Instance, InstanceStatus
from .exceptions import AuthenticationError, RegionError, InstanceError


class IBMCloudClient:
    """
    Wrapper around IBM VPC SDK with automatic token refresh,
    region management, and error handling.
    """

    TOKEN_LIFETIME_MINUTES = 20  # IAM tokens expire after 20 minutes
    TOKEN_REFRESH_BUFFER_MINUTES = 2  # Refresh 2 minutes before expiry

    def __init__(self, api_key: str):
        """
        Initialize client with IBM Cloud API key

        Args:
            api_key: IBM Cloud API key for authentication

        Raises:
            AuthenticationError: If authentication fails
        """
        self.api_key = api_key
        self._service: Optional[VpcV1] = None
        self._current_region: Optional[str] = None
        self._last_auth_time: Optional[datetime] = None
        self._authenticate()

    def _authenticate(self) -> None:
        """Authenticate and create VPC service instance"""
        try:
            authenticator = IAMAuthenticator(self.api_key)

            # Use yesterday's date for API version (common IBM Cloud pattern)
            today = datetime.now()
            version_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")

            self._service = VpcV1(
                authenticator=authenticator,
                version=version_date
            )
            self._last_auth_time = datetime.now()
        except Exception as e:
            raise AuthenticationError(f"Failed to authenticate with IBM Cloud: {e}")

    def _check_token_refresh(self) -> None:
        """Refresh authentication if token is about to expire"""
        if self._last_auth_time:
            elapsed = datetime.now() - self._last_auth_time
            elapsed_minutes = elapsed.total_seconds() / 60
            threshold = self.TOKEN_LIFETIME_MINUTES - self.TOKEN_REFRESH_BUFFER_MINUTES

            if elapsed_minutes > threshold:
                self._authenticate()

    def set_region(self, region_name: str) -> None:
        """
        Set the active region for API calls

        Args:
            region_name: Region identifier (e.g., 'us-south', 'eu-gb')

        Raises:
            RegionError: If region is invalid or cannot be set
        """
        try:
            region_url = f"https://{region_name}.iaas.cloud.ibm.com/v1"
            self._service.set_service_url(region_url)
            self._current_region = region_name
        except Exception as e:
            raise RegionError(f"Failed to set region {region_name}: {e}")

    async def list_regions(self) -> List[Region]:
        """
        Fetch all available VPC regions

        Returns:
            List of Region objects sorted by name

        Raises:
            RegionError: If regions cannot be fetched
        """
        self._check_token_refresh()
        try:
            response = self._service.list_regions()
            regions = []
            for region_data in response.get_result()['regions']:
                regions.append(Region(
                    name=region_data['name'],
                    endpoint=region_data['endpoint'],
                    status=region_data['status']
                ))
            return sorted(regions, key=lambda r: r.name)
        except ApiException as e:
            raise RegionError(f"Failed to list regions: {e.message if hasattr(e, 'message') else e}")
        except Exception as e:
            raise RegionError(f"Unexpected error listing regions: {e}")

    async def list_instances(self, region: Optional[str] = None) -> List[Instance]:
        """
        Fetch all VPC instances in the current or specified region

        Args:
            region: Optional region to list instances from (switches if different)

        Returns:
            List of Instance objects

        Raises:
            InstanceError: If instances cannot be fetched
        """
        if region and region != self._current_region:
            self.set_region(region)

        self._check_token_refresh()
        try:
            response = self._service.list_instances()
            instances = []
            for inst_data in response.get_result()['instances']:
                instances.append(self._parse_instance(inst_data))
            return instances
        except ApiException as e:
            raise InstanceError(f"Failed to list instances: {e.message if hasattr(e, 'message') else e}")
        except Exception as e:
            raise InstanceError(f"Unexpected error listing instances: {e}")

    async def get_instance(self, instance_id: str) -> Instance:
        """
        Fetch detailed information for a specific instance

        Args:
            instance_id: Instance UUID

        Returns:
            Instance object with full details

        Raises:
            InstanceError: If instance cannot be fetched
        """
        self._check_token_refresh()
        try:
            response = self._service.get_instance(id=instance_id)
            return self._parse_instance(response.get_result())
        except ApiException as e:
            raise InstanceError(f"Failed to get instance {instance_id}: {e.message if hasattr(e, 'message') else e}")
        except Exception as e:
            raise InstanceError(f"Unexpected error getting instance: {e}")

    async def start_instance(self, instance_id: str) -> Dict[str, Any]:
        """
        Start a stopped instance

        Args:
            instance_id: Instance UUID

        Returns:
            Dict with action result

        Raises:
            InstanceError: If start action fails
        """
        return await self._instance_action(instance_id, "start")

    async def stop_instance(self, instance_id: str) -> Dict[str, Any]:
        """
        Stop a running instance

        Args:
            instance_id: Instance UUID

        Returns:
            Dict with action result

        Raises:
            InstanceError: If stop action fails
        """
        return await self._instance_action(instance_id, "stop")

    async def reboot_instance(self, instance_id: str) -> Dict[str, Any]:
        """
        Reboot a running instance

        Args:
            instance_id: Instance UUID

        Returns:
            Dict with action result

        Raises:
            InstanceError: If reboot action fails
        """
        return await self._instance_action(instance_id, "reboot")

    async def _instance_action(self, instance_id: str, action: str) -> Dict[str, Any]:
        """
        Execute an action on an instance

        Args:
            instance_id: Instance UUID
            action: Action type (start, stop, reboot)

        Returns:
            Dict with action result

        Raises:
            InstanceError: If action fails
        """
        self._check_token_refresh()
        try:
            response = self._service.create_instance_action(
                instance_id=instance_id,
                type=action
            )
            return response.get_result()
        except ApiException as e:
            raise InstanceError(f"Failed to {action} instance {instance_id}: {e.message if hasattr(e, 'message') else e}")
        except Exception as e:
            raise InstanceError(f"Unexpected error during {action}: {e}")

    def _parse_instance(self, data: Dict[str, Any]) -> Instance:
        """
        Parse raw API response into Instance model

        Args:
            data: Raw instance data from API

        Returns:
            Instance object
        """
        # Extract primary network interface IP
        primary_ip = None
        if data.get('primary_network_interface'):
            pni = data['primary_network_interface']
            if pni.get('primary_ip'):
                primary_ip = pni['primary_ip'].get('address')

        # Parse status into enum
        status_value = data.get('status', 'pending')
        try:
            status = InstanceStatus(status_value)
        except ValueError:
            # Fallback for unknown statuses
            status = InstanceStatus.PENDING

        return Instance(
            id=data['id'],
            name=data['name'],
            status=status,
            zone=data['zone']['name'],
            vpc_name=data['vpc']['name'],
            vpc_id=data['vpc']['id'],
            profile=data['profile']['name'],
            primary_ip=primary_ip,
            created_at=data['created_at'],
            crn=data['crn']
        )

    @property
    def current_region(self) -> Optional[str]:
        """Get the currently selected region"""
        return self._current_region
