"""IBM Cloud Resource Manager API Client"""
from typing import List
import requests
import json
from pathlib import Path
from icecream import ic

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
        self._account_id: str = None

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

    def _get_account_id(self) -> str:
        """
        Get account ID from the API key using IAM API

        Returns:
            Account ID string

        Raises:
            AuthenticationError: If account ID retrieval fails
        """
        if self._account_id:
            return self._account_id

        try:
            token = self._get_iam_token()
            
            # Get API key details to extract account_id using IAM Identity Services API
            # The API key details endpoint returns account_id
            response = requests.get(
                "https://iam.cloud.ibm.com/v1/apikeys/details",
                headers={
                    "Authorization": f"Bearer {token}",
                    "IAM-Apikey": self.api_key,
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            api_key_details = response.json()
            
            # Extract account_id from the response
            account_id = api_key_details.get("account_id")
            
            if not account_id:
                # Fallback: try to decode JWT token to get account info
                import base64
                try:
                    # JWT tokens have 3 parts separated by dots
                    token_parts = token.split('.')
                    if len(token_parts) >= 2:
                        # Decode the payload (second part), add padding if needed
                        payload = token_parts[1]
                        payload += '=' * (4 - len(payload) % 4)  # Add padding
                        payload_decoded = base64.urlsafe_b64decode(payload)
                        token_data = json.loads(payload_decoded)
                        # Try different possible paths for account_id in token
                        account_id = (
                            token_data.get("account", {}).get("bss") or
                            token_data.get("account_id") or
                            token_data.get("accountId")
                        )
                except Exception as decode_err:
                    ic(f"Failed to decode token for account_id: {decode_err}")
            
            if not account_id:
                raise AuthenticationError("Could not extract account_id from API key or token")
            
            self._account_id = account_id
            ic(f"Retrieved account_id: {account_id}")
            return self._account_id
        except Exception as e:
            ic(f"Error getting account_id: {e}")
            raise AuthenticationError(f"Failed to get account ID: {e}")

    async def list_resource_groups(self) -> List[ResourceGroup]:
        """
        List all resource groups for the account
        
        Uses the Resource Controller API v2 endpoint to fetch all resource groups
        accessible to the authenticated account.

        Returns:
            List of ResourceGroup objects

        Raises:
            Exception: If resource groups cannot be fetched
        """
        try:
            token = self._get_iam_token()
            
            # Get account_id from API key
            account_id = self._get_account_id()
            ic(f"Fetching resource groups from Resource Controller API for account {account_id}")
            
            # The Resource Controller API requires account_id parameter
            response = requests.get(
                f"{self.BASE_URL}/resource_groups",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                params={
                    "account_id": account_id
                }
            )
            ic(f"Resource groups API response status: {response.status_code}")
            response.raise_for_status()

            json_data = response.json()
            ic(f"Resource groups API response keys: {json_data.keys() if isinstance(json_data, dict) else 'list'}")
            
            resource_groups = []
            # The API returns {"resources": [...]} format
            rg_list = json_data.get("resources", [])
            if not rg_list and isinstance(json_data, list):
                rg_list = json_data
            
            ic(f"Found {len(rg_list)} resource groups in response")
            
            for rg_data in rg_list:
                try:
                    resource_groups.append(ResourceGroup(
                        id=rg_data["id"],
                        name=rg_data["name"],
                        state=rg_data.get("state", "active"),
                        crn=rg_data.get("crn", "")
                    ))
                except KeyError as e:
                    ic(f"Missing required field in resource group data: {e}", rg_data)
                    continue

            ic(f"Successfully parsed {len(resource_groups)} resource groups")
            return sorted(resource_groups, key=lambda rg: rg.name)
        except requests.exceptions.HTTPError as e:
            ic(f"HTTP error fetching resource groups: {e}", f"Response: {e.response.text if hasattr(e, 'response') else 'N/A'}")
            raise Exception(f"Failed to list resource groups: HTTP {e.response.status_code if hasattr(e, 'response') else 'unknown'}")
        except Exception as e:
            ic(f"Exception in list_resource_groups: {e}")
            raise Exception(f"Failed to list resource groups: {e}")
