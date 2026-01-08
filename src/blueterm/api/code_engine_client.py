"""IBM Cloud Code Engine API Client"""
from typing import List, Optional
from datetime import datetime
import requests
from icecream import ic

from .models import (
    Region, Instance, InstanceStatus,
    CodeEngineProject, CodeEngineApp, CodeEngineJob, CodeEngineBuild
)
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
        
        Code Engine supports the same regions as VPC. We use the VPC API
        to get all available regions, then map them to Code Engine endpoints.

        Returns:
            List of Region objects
        """
        # Code Engine supports all VPC regions
        # Map of region names to Code Engine endpoints
        code_engine_endpoints = {
            "us-south": "https://api.us-south.codeengine.cloud.ibm.com",
            "us-east": "https://api.us-east.codeengine.cloud.ibm.com",
            "eu-gb": "https://api.eu-gb.codeengine.cloud.ibm.com",
            "eu-de": "https://api.eu-de.codeengine.cloud.ibm.com",
            "jp-tok": "https://api.jp-tok.codeengine.cloud.ibm.com",
            "au-syd": "https://api.au-syd.codeengine.cloud.ibm.com",
            "br-sao": "https://api.br-sao.codeengine.cloud.ibm.com",
            "ca-mon": "https://api.ca-mon.codeengine.cloud.ibm.com",
            "ca-tor": "https://api.ca-tor.codeengine.cloud.ibm.com",
            "eu-es": "https://api.eu-es.codeengine.cloud.ibm.com",
            "jp-osa": "https://api.jp-osa.codeengine.cloud.ibm.com",
        }
        
        # Try to get regions from VPC API if available, otherwise use known regions
        try:
            # Import here to avoid circular dependency
            from ibm_vpc import VpcV1
            from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
            from datetime import datetime, timedelta
            
            authenticator = IAMAuthenticator(self.api_key)
            today = datetime.now()
            version_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
            vpc_service = VpcV1(authenticator=authenticator, version=version_date)
            
            # Use us-south endpoint to get all regions
            vpc_service.set_service_url("https://us-south.iaas.cloud.ibm.com/v1")
            regions_response = vpc_service.list_regions()
            
            regions = []
            for region_data in regions_response.get_result()["regions"]:
                region_name = region_data["name"]
                if region_name in code_engine_endpoints:
                    regions.append(Region(
                        name=region_name,
                        endpoint=code_engine_endpoints[region_name],
                        status=region_data.get("status", "available")
                    ))
            
            if regions:
                ic(f"Loaded {len(regions)} Code Engine regions from VPC API")
                return sorted(regions, key=lambda r: r.name)
        except Exception as e:
            ic(f"Failed to fetch regions from VPC API, using known regions: {e}")
        
        # Fallback to known regions
        return [
            Region(name="us-south", endpoint="https://api.us-south.codeengine.cloud.ibm.com", status="available"),
            Region(name="us-east", endpoint="https://api.us-east.codeengine.cloud.ibm.com", status="available"),
            Region(name="eu-gb", endpoint="https://api.eu-gb.codeengine.cloud.ibm.com", status="available"),
            Region(name="eu-de", endpoint="https://api.eu-de.codeengine.cloud.ibm.com", status="available"),
            Region(name="jp-tok", endpoint="https://api.jp-tok.codeengine.cloud.ibm.com", status="available"),
            Region(name="au-syd", endpoint="https://api.au-syd.codeengine.cloud.ibm.com", status="available"),
            Region(name="br-sao", endpoint="https://api.br-sao.codeengine.cloud.ibm.com", status="available"),
            Region(name="ca-mon", endpoint="https://api.ca-mon.codeengine.cloud.ibm.com", status="available"),
            Region(name="ca-tor", endpoint="https://api.ca-tor.codeengine.cloud.ibm.com", status="available"),
            Region(name="eu-es", endpoint="https://api.eu-es.codeengine.cloud.ibm.com", status="available"),
            Region(name="jp-osa", endpoint="https://api.jp-osa.codeengine.cloud.ibm.com", status="available"),
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

    async def list_projects(self, resource_group_id: Optional[str] = None) -> List[CodeEngineProject]:
        """
        List Code Engine projects in a resource group or all projects in the region

        Args:
            resource_group_id: Optional resource group ID (uses set resource group if not provided)
                              If not provided, lists all projects in the region

        Returns:
            List of CodeEngineProject objects
        """
        if not resource_group_id:
            resource_group_id = self._resource_group_id

        try:
            token = self._get_iam_token()
            region = self._current_region or "us-south"

            # Build API URL
            url = f"https://api.{region}.codeengine.cloud.ibm.com/v2/projects"
            
            # Code Engine API does NOT support resource_group_id as a query parameter
            # It returns all projects in the region, and we filter client-side if needed
            params = {
                "limit": 100
            }
            
            ic(f"Fetching Code Engine projects from {url} (all projects in region)")
            if resource_group_id:
                ic(f"Will filter projects by resource_group_id: {resource_group_id} client-side")

            ic(f"API request params: {params}")

            response = requests.get(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                params=params
            )
            
            ic(f"Code Engine projects API response status: {response.status_code}")
            ic(f"Code Engine projects API response URL: {response.url}")
            
            response.raise_for_status()

            data = response.json()
            ic(f"Code Engine projects API response keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
            
            # The API returns {"projects": [...]} format
            projects_data = data.get("projects", [])
            
            # If projects is not in the response, check if data is a list directly
            if not projects_data and isinstance(data, list):
                projects_data = data
            
            ic(f"Found {len(projects_data)} projects in API response")
            
            projects = []
            for proj_data in projects_data:
                # Extract resource group ID from project data
                # The API returns it as "resource_group_id" or "resource_group"
                proj_rg_id = proj_data.get("resource_group_id") or proj_data.get("resource_group")
                
                # Filter by resource group if specified (API returns all projects, filter client-side)
                if resource_group_id:
                    if not proj_rg_id or proj_rg_id != resource_group_id:
                        ic(f"Skipping project {proj_data.get('name')} - resource group mismatch: {proj_rg_id} != {resource_group_id}")
                        continue
                    
                project = CodeEngineProject(
                    id=proj_data.get("id", ""),
                    name=proj_data.get("name", ""),
                    region=proj_data.get("region", region),
                    resource_group_id=proj_rg_id or resource_group_id or "",
                    status=proj_data.get("status", "active"),
                    created_at=proj_data.get("created_at", ""),
                    crn=proj_data.get("crn", ""),
                    entity_tag=proj_data.get("entity_tag")
                )
                projects.append(project)
                ic(f"Added project: {project.name} (resource_group_id: {project.resource_group_id})")
            
            ic(f"Loaded {len(projects)} Code Engine projects after filtering")
            return projects
        except requests.exceptions.HTTPError as e:
            ic(f"HTTP error fetching Code Engine projects: {e}")
            if hasattr(e, 'response') and e.response is not None:
                ic(f"Response status: {e.response.status_code}")
                ic(f"Response text: {e.response.text[:500]}")
            return []
        except Exception as e:
            ic(f"Error fetching Code Engine projects: {e}")
            import traceback
            ic(f"Traceback: {traceback.format_exc()}")
            return []

    async def list_apps(self, project_id: str) -> List[CodeEngineApp]:
        """
        List applications in a Code Engine project

        Args:
            project_id: Code Engine project ID

        Returns:
            List of CodeEngineApp objects
        """
        try:
            token = self._get_iam_token()
            region = self._current_region or "us-south"

            response = requests.get(
                f"https://api.{region}.codeengine.cloud.ibm.com/v2/projects/{project_id}/applications",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                params={
                    "limit": 100
                }
            )
            response.raise_for_status()

            data = response.json()
            apps_data = data.get("applications", [])
            
            apps = []
            for app_data in apps_data:
                app = CodeEngineApp(
                    id=app_data.get("id", ""),
                    name=app_data.get("name", ""),
                    project_id=project_id,
                    status=app_data.get("status", "ready"),
                    created_at=app_data.get("created_at", ""),
                    updated_at=app_data.get("updated_at"),
                    entity_tag=app_data.get("entity_tag")
                )
                apps.append(app)
            
            ic(f"Loaded {len(apps)} applications for project {project_id}")
            return apps
        except Exception as e:
            ic(f"Error fetching Code Engine applications: {e}")
            return []

    async def list_jobs(self, project_id: str) -> List[CodeEngineJob]:
        """
        List jobs in a Code Engine project

        Args:
            project_id: Code Engine project ID

        Returns:
            List of CodeEngineJob objects
        """
        try:
            token = self._get_iam_token()
            region = self._current_region or "us-south"

            response = requests.get(
                f"https://api.{region}.codeengine.cloud.ibm.com/v2/projects/{project_id}/jobs",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                params={
                    "limit": 100
                }
            )
            response.raise_for_status()

            data = response.json()
            jobs_data = data.get("jobs", [])
            
            jobs = []
            for job_data in jobs_data:
                job = CodeEngineJob(
                    id=job_data.get("id", ""),
                    name=job_data.get("name", ""),
                    project_id=project_id,
                    status=job_data.get("status", "ready"),
                    created_at=job_data.get("created_at", ""),
                    updated_at=job_data.get("updated_at"),
                    entity_tag=job_data.get("entity_tag")
                )
                jobs.append(job)
            
            ic(f"Loaded {len(jobs)} jobs for project {project_id}")
            return jobs
        except Exception as e:
            ic(f"Error fetching Code Engine jobs: {e}")
            return []

    async def list_builds(self, project_id: str) -> List[CodeEngineBuild]:
        """
        List builds in a Code Engine project

        Args:
            project_id: Code Engine project ID

        Returns:
            List of CodeEngineBuild objects
        """
        try:
            token = self._get_iam_token()
            region = self._current_region or "us-south"

            response = requests.get(
                f"https://api.{region}.codeengine.cloud.ibm.com/v2/projects/{project_id}/builds",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                params={
                    "limit": 100
                }
            )
            response.raise_for_status()

            data = response.json()
            builds_data = data.get("builds", [])
            
            builds = []
            for build_data in builds_data:
                build = CodeEngineBuild(
                    id=build_data.get("id", ""),
                    name=build_data.get("name", ""),
                    project_id=project_id,
                    status=build_data.get("status", "ready"),
                    created_at=build_data.get("created_at", ""),
                    updated_at=build_data.get("updated_at"),
                    entity_tag=build_data.get("entity_tag")
                )
                builds.append(build)
            
            ic(f"Loaded {len(builds)} builds for project {project_id}")
            return builds
        except Exception as e:
            ic(f"Error fetching Code Engine builds: {e}")
            return []

    async def list_secrets(self, project_id: str) -> List[dict]:
        """
        List secrets in a Code Engine project

        Args:
            project_id: Code Engine project ID

        Returns:
            List of secret dictionaries
        """
        try:
            token = self._get_iam_token()
            region = self._current_region or "us-south"

            response = requests.get(
                f"https://api.{region}.codeengine.cloud.ibm.com/v2/projects/{project_id}/secrets",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                params={
                    "limit": 100
                }
            )
            response.raise_for_status()

            data = response.json()
            secrets_data = data.get("secrets", [])
            
            ic(f"Loaded {len(secrets_data)} secrets for project {project_id}")
            return secrets_data
        except Exception as e:
            ic(f"Error fetching Code Engine secrets: {e}")
            return []

    async def list_instances(self, region: Optional[str] = None) -> List[Instance]:
        """
        List Code Engine projects as Instance objects (for compatibility with existing UI)

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
                id=project.id,
                name=project.name,
                status=status_map.get(project.status, InstanceStatus.PENDING),
                zone=project.region,
                vpc_name="Code Engine",  # Use service name
                vpc_id=project.resource_group_id,
                profile="Project",  # Resource type
                primary_ip=None,  # Not applicable for Code Engine
                created_at=project.created_at,
                crn=project.crn
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
