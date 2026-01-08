"""IBM Cloud Resource Manager API Client"""
from typing import List
import requests

from .models import ResourceGroup
from .exceptions import AuthenticationError


class ResourceManagerClient:
    """
    Client for IBM Cloud Resource Manager API.

    Used to fetch resource groups which are required for Code Engine and other services.
    """

    BASE_URL = "https://resource-controller.cloud.ibm.com/v2"

    def __init__(self, api_key: str):
        """
        Initialize Resource Manager client with IBM Cloud API key

        Args:
            api_key: IBM Cloud API key for authentication

        Raises:
            AuthenticationError: If authentication fails
        """
        self.api_key = api_key
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

    async def list_resource_groups(self) -> List[ResourceGroup]:
        """
        List all resource groups for the account

        Returns:
            List of ResourceGroup objects

        Raises:
            Exception: If resource groups cannot be fetched
        """
        try:
            token = self._get_iam_token()
            response = requests.get(
                f"{self.BASE_URL}/resource_groups",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()

            resource_groups = []
            for rg_data in response.json().get("resources", []):
                resource_groups.append(ResourceGroup(
                    id=rg_data["id"],
                    name=rg_data["name"],
                    state=rg_data["state"],
                    crn=rg_data["crn"]
                ))

            return sorted(resource_groups, key=lambda rg: rg.name)
        except Exception as e:
            raise Exception(f"Failed to list resource groups: {e}")
