"""Main Blueterm Application"""
from typing import Optional, List
import json
import asyncio
from pathlib import Path

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer
from textual.worker import Worker, WorkerState
from textual.theme import Theme
from icecream import ic
import logging

# Get the package directory for CSS path
# Handle both installed package and source development
PACKAGE_DIR = Path(__file__).parent
# If CSS doesn't exist in package dir, try source location (for development)
CSS_SOURCE_PATH = PACKAGE_DIR / "styles" / "app.tcss"
if not CSS_SOURCE_PATH.exists():
    # Try source location (when running from source)
    SOURCE_DIR = Path(__file__).parent.parent.parent.parent / "src" / "blueterm"
    CSS_SOURCE_PATH = SOURCE_DIR / "styles" / "app.tcss"

from .config import Config, UserPreferences
from .api.client import IBMCloudClient
from .api.iks_client import IKSClient
from .api.roks_client import ROKSClient
from .api.code_engine_client import CodeEngineClient
from .api.resource_manager_client import ResourceManagerClient
from .api.models import (
    Region, Instance, ResourceGroup, InstanceStatus,
    CodeEngineProject, CodeEngineApp, CodeEngineJob, CodeEngineBuild, CodeEngineSecret
)
from .api.exceptions import AuthenticationError, ConfigurationError
from .widgets.region_selector import RegionSelector
from .widgets.resource_type_selector import ResourceTypeSelector, ResourceType
from .widgets.info_bar import InfoBar
from .widgets.instance_table import InstanceTable, ResourceType as TableResourceType
from .widgets.status_bar import StatusBar
from .widgets.search_input import SearchInput
from .widgets.detail_panel import DetailPanel
from .screens.detail_screen import DetailScreen
from .screens.confirm_screen import ConfirmScreen
from .screens.error_screen import ErrorScreen
from .screens.code_engine_project_detail_screen import CodeEngineProjectDetailScreen
from .screens.resource_group_selection_screen import ResourceGroupSelectionScreen


class BluetermApp(App):
    """
    Blueterm - IBM Cloud Resource Manager TUI

    Keyboard Bindings:
        Resource Types:
            v: Switch to VPC
            i: Switch to IKS
            o: Switch to ROKS
            c: Switch to Code Engine

        Top Navigation:
            r: Focus regions selector
            g: Focus resource group selector
            h/l or ←/→: Navigate within focused section
            0-9: Jump to region by number (when regions focused)

        Instance Navigation:
            j/k or ↑/↓: Navigate instances/resources
            h/l or ←/→: Switch regions (when not focused)

        Actions:
            d: View instance details
            s: Start instance
            S: Stop instance
            b: Reboot instance
            R: Refresh current view

        General:
            q: Quit application
            ?: Show help
            Ctrl+b: Toggle sidebar
    """

    CSS_PATH = str(CSS_SOURCE_PATH)
    TITLE = "Blueterm - IBM Cloud VPC Manager"

    # IBM Carbon Design System Theme
    # Based on Carbon dark theme (Gray 100 background)
    IBM_CARBON_THEME = Theme(
        name="ibm-carbon",
        primary="#0f62fe",           # Blue 60 - IBM brand blue
        secondary="#393939",         # Gray 80
        warning="#f1c21b",           # Yellow 30
        error="#da1e28",             # Red 60
        success="#24a148",           # Green 50
        accent="#78a9ff",            # Blue 40 - lighter for contrast
        foreground="#f4f4f4",        # Gray 10 - main text
        background="#161616",        # Gray 100 - darkest background
        surface="#262626",           # Gray 90 - surface/panel
        panel="#262626",             # Gray 90 - same as surface
        dark=True,
        variables={
            "text-muted": "#c6c6c6",  # Gray 30 - secondary text
        }
    )

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("question_mark", "help", "Help"),
        Binding("slash", "search", "Search"),
        # Resource type switching (numbers)
        Binding("1", "switch_resource_type('1')", "VPC", show=True),
        Binding("2", "switch_resource_type('2')", "IKS", show=True),
        Binding("3", "switch_resource_type('3')", "ROKS", show=True),
        Binding("4", "switch_resource_type('4')", "Code Engine", show=True),
        # Instance actions
        Binding("b", "reboot_instance", "Reboot"),
        Binding("s", "start_instance", "Start"),
        Binding("S", "stop_instance", "Stop"),
        Binding("R", "refresh", "Refresh"),
        Binding("d", "show_details", "Details"),
        Binding("enter", "select_project", "Select", show=False),
        Binding("h", "region_previous", "Prev Region", show=False),
        Binding("l", "region_next", "Next Region", show=False),
        Binding("left", "region_previous", show=False),
        Binding("right", "region_next", show=False),
        # Number keys for quick region switching (0, 5-9 when regions focused)
        # Note: 1-4 are used for resource type switching
        Binding("0", "region_number(0)", show=False),
        Binding("5", "region_number(5)", show=False),
        Binding("6", "region_number(6)", show=False),
        Binding("7", "region_number(7)", show=False),
        Binding("8", "region_number(8)", show=False),
        Binding("9", "region_number(9)", show=False),
        Binding("t", "cycle_theme", "Theme"),
        Binding("a", "toggle_auto_refresh", "Auto-refresh"),
        # Code Engine navigation
        Binding("escape", "back_to_projects", "Back", show=False),
        # Interactive navigation
        Binding("r", "focus_region", "Focus Region", show=True),
        Binding("g", "focus_resource_group", "Focus RG", show=True),
        Binding("ctrl+b", "toggle_sidebar", "Toggle Sidebar", show=True),
    ]

    # Available color themes
    THEMES = [
        "ibm-carbon",         # IBM Carbon Design System (default)
        "textual-dark",
        "textual-light",
        "nord",
        "gruvbox",
        "catppuccin-mocha",
        "dracula",
        "tokyo-night",
        "monokai",
        "solarized-light",
    ]

    def __init__(self):
        super().__init__()

        # Register IBM Carbon theme
        self.register_theme(self.IBM_CARBON_THEME)

        try:
            self.config = Config.from_env()
            self.config.validate()
            
            # Setup debug logging if enabled (file only, no console output)
            if self.config.debug:
                debug_log_file = Path.home() / ".blueterm" / "debug.log"
                logging.basicConfig(
                    level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(debug_log_file),
                        # No StreamHandler - we don't want console output
                    ],
                    force=True  # Override any existing logging config
                )
                ic("Debug logging enabled (file only)")
            else:
                # Configure logging to only write to file, not console
                log_file = Path.home() / ".blueterm" / "blueterm.log"
                logging.basicConfig(
                    level=logging.WARNING,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(log_file),
                        # No StreamHandler
                    ],
                    force=True
                )

            # Initialize all API clients
            self.vpc_client = IBMCloudClient(self.config.api_key)
            self.iks_client = IKSClient(self.config.api_key)
            self.roks_client = ROKSClient(self.config.api_key)
            self.code_engine_client = CodeEngineClient(self.config.api_key)
            self.resource_manager_client = ResourceManagerClient(self.config.api_key)

            # Set current client to VPC by default
            self.client = self.vpc_client
            self.current_resource_type = ResourceType.VPC

        except (ConfigurationError, AuthenticationError) as e:
            self.exit(1, str(e))
            return

        # Load user preferences
        self.preferences = UserPreferences.load()

        # Set theme from preferences
        if self.preferences.theme in self.THEMES:
            self.current_theme_index = self.THEMES.index(self.preferences.theme)
        else:
            self.current_theme_index = 0
            self.preferences.theme = self.THEMES[0]

        self.regions: List[Region] = []
        self.current_region: Optional[Region] = None
        self.resource_groups: List[ResourceGroup] = []
        self.current_resource_group: Optional[ResourceGroup] = None
        self.instances: List[Instance] = []
        self.filtered_instances: List[Instance] = []
        self.search_query: str = ""
        self._refresh_timer = None  # Auto-refresh timer
        
        # Code Engine specific state
        self.selected_project: Optional[CodeEngineProject] = None
        self.project_apps: List[CodeEngineApp] = []
        self.project_jobs: List[CodeEngineJob] = []
        self.project_builds: List[CodeEngineBuild] = []
        self.project_secrets: List[CodeEngineSecret] = []
        self.project_resources_view: str = "apps"  # "apps", "jobs", "builds", "secrets"
        self.project_counts: dict = {}  # Cache of project counts {project_id: {apps: N, jobs: N, ...}}
        
        # Interactive navigation state
        self.focused_section: Optional[str] = None  # None, "region", "resource_group"

    def compose(self) -> ComposeResult:
        """Compose the main application layout with left sidebar"""
        yield Header()
        yield InfoBar(id="info_bar")
        with Horizontal(id="app_layout"):
            # Left sidebar for resource type selection
            yield ResourceTypeSelector(id="resource_type_selector")

            # Main content area (right side)
            with Vertical(id="main_container"):
                yield RegionSelector(id="region_selector")
                yield InstanceTable(id="instance_table")
                yield SearchInput(id="search_input")

        yield StatusBar(id="status_bar")
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize application on mount"""
        self.title = self.TITLE

        # Set theme from preferences
        self.theme = self.preferences.theme

        # Update theme display in region selector
        try:
            region_selector = self.query_one("#region_selector", RegionSelector)
            region_selector.set_theme(self.preferences.theme)
        except:
            pass

        # Start time update timer (update every second)
        self.set_interval(1.0, self._update_time_display)

        # Load regions first (needed for UI display)
        self.load_regions()
        
        # Load resource groups after regions (needed for Code Engine)
        # Note: load_resource_groups is a worker, so it runs asynchronously
        # We'll set resource groups on region selector when they load
        self.load_resource_groups()

        # Start auto-refresh if enabled
        if self.preferences.auto_refresh_enabled:
            self._start_auto_refresh()

    def _update_time_display(self) -> None:
        """Update the time display in info bar"""
        try:
            info_bar = self.query_one("#info_bar", InfoBar)
            info_bar.update_time()
        except:
            pass

    @work(thread=True)
    async def load_resource_groups(self) -> None:
        """Load available resource groups from API"""
        try:
            # Access UI directly (Textual workers handle thread safety)
            status_bar = self.query_one("#status_bar", StatusBar)
            status_bar.set_loading(True)

            self.resource_groups = await self.resource_manager_client.list_resource_groups()
            ic(f"Loaded {len(self.resource_groups)} resource groups")

            if self.resource_groups:
                # Select first resource group by default
                self.current_resource_group = self.resource_groups[0]
                ic(f"Selected resource group: {self.current_resource_group.name}")

                # Set resource group on Code Engine client
                self.code_engine_client.set_resource_group(self.current_resource_group.id)

                # Update region selector and InfoBar (must be done in main thread)
                def update_ui():
                    try:
                        region_selector = self.query_one("#region_selector", RegionSelector)
                        ic(f"Setting {len(self.resource_groups)} resource groups on region selector")
                        region_selector.set_resource_groups(self.resource_groups, self.current_resource_group)
                        ic(f"Resource groups set on region selector")
                    except Exception as e:
                        import traceback
                        ic(f"ERROR: Failed to update region selector with resource groups: {e}")
                        ic(f"Traceback: {traceback.format_exc()}")
                    
                    try:
                        info_bar = self.query_one("#info_bar", InfoBar)
                        info_bar.set_resource_group(self.current_resource_group)
                    except Exception as e:
                        ic(f"Warning: Failed to update info bar with resource group: {e}")

                self.call_from_thread(update_ui)
            else:
                ic("No resource groups returned from API")

            # Update status bar (Textual workers handle thread safety)
            status_bar = self.query_one("#status_bar", StatusBar)
            status_bar.set_loading(False)

        except Exception as e:
            # Non-fatal error - resource groups are optional for VPC/IKS/ROKS
            ic(f"ERROR: Failed to load resource groups: {e}")
            # Show error in status bar
            def show_error():
                try:
                    status_bar = self.query_one("#status_bar", StatusBar)
                    status_bar.set_loading(False)
                    status_bar.set_message(f"Warning: Could not load resource groups: {str(e)[:50]}", "warning")
                except:
                    pass
            self.call_from_thread(show_error)

    @work(thread=True, exclusive=True)
    async def load_regions(self) -> None:
        """Load available regions from API"""
        try:
            status_bar = self.query_one("#status_bar", StatusBar)
            status_bar.set_loading(True)

            self.regions = await self.client.list_regions()
            ic(f"Loaded {len(self.regions)} regions from API")

            # Set default region
            default = next(
                (r for r in self.regions if r.name == self.config.default_region),
                self.regions[0] if self.regions else None
            )

            if default:
                self.current_region = default
                self.client.set_region(default.name)
                # Also set region on Code Engine client if it's the active resource type
                if self.current_resource_type == ResourceType.CODE_ENGINE:
                    self.code_engine_client.set_region(default.name)

                region_selector = self.query_one("#region_selector", RegionSelector)
                ic(f"Region selector found, setting {len(self.regions)} regions")
                region_selector.set_regions(self.regions, default)
                ic(f"Set {len(self.regions)} regions on region selector")
                ic(f"Regions: {[r.name for r in self.regions]}")
                ic(f"Region selector has {len(region_selector.regions)} regions after set_regions")
                
                # Also set resource groups if available
                if self.resource_groups:
                    ic(f"Setting {len(self.resource_groups)} resource groups on region selector")
                    region_selector.set_resource_groups(self.resource_groups, self.current_resource_group)
                    ic(f"Region selector has {len(region_selector.resource_groups)} resource groups after set_resource_groups")
                else:
                    ic("No resource groups available to set")
                

                # Update info bar with region and resource group
                try:
                    info_bar = self.query_one("#info_bar", InfoBar)
                    info_bar.set_region(default)
                    info_bar.set_resource_group(self.current_resource_group)
                except:
                    pass

                self.load_instances()
            else:
                # Use call_from_thread to safely push screen from worker thread
                # Create ErrorScreen in main thread via lambda
                self.call_from_thread(
                    lambda: self.push_screen(
                        ErrorScreen(
                            "No regions available",
                            recoverable=False,
                            suggestion="Check your IBM Cloud account configuration"
                        )
                    )
                )

            status_bar.set_loading(False)

        except Exception as e:
            # Use call_from_thread to safely push screen from worker thread
            # Create ErrorScreen in main thread via lambda
            self.call_from_thread(
                lambda: self.push_screen(
                    ErrorScreen(
                        f"Failed to load regions: {e}",
                        recoverable=False,
                        suggestion="Check your IBMCLOUD_API_KEY and network connectivity"
                    )
                )
            )

    @work(thread=True, exclusive=True)
    async def load_instances(self) -> None:
        """Load instances for current region"""
        if not self.current_region:
            return

        try:
            status_bar = self.query_one("#status_bar", StatusBar)
            status_bar.set_loading(True)

            # For Code Engine, ensure resource group and region are set
            if self.current_resource_type == ResourceType.CODE_ENGINE:
                # Set region on Code Engine client
                if self.code_engine_client._current_region != self.current_region.name:
                    ic(f"Setting region on Code Engine client: {self.current_region.name}")
                    self.code_engine_client.set_region(self.current_region.name)
                
                if not self.current_resource_group:
                    ic("No resource group set for Code Engine - trying to load all projects")
                    # Don't return - let it try to load all projects in the region
                else:
                    # Ensure Code Engine client has the resource group set
                    if self.code_engine_client._resource_group_id != self.current_resource_group.id:
                        ic(f"Setting resource group on Code Engine client: {self.current_resource_group.id}")
                        self.code_engine_client.set_resource_group(self.current_resource_group.id)

            self.instances = await self.client.list_instances(self.current_region.name)
            self.apply_search_filter()

            instance_table = self.query_one("#instance_table", InstanceTable)
            
            # Set resource type on table to configure columns
            table_resource_type_map = {
                ResourceType.VPC: TableResourceType.VPC,
                ResourceType.IKS: TableResourceType.IKS,
                ResourceType.ROKS: TableResourceType.ROKS,
                ResourceType.CODE_ENGINE: TableResourceType.CODE_ENGINE,
            }
            instance_table.set_resource_type(table_resource_type_map[self.current_resource_type])
            
            # For Code Engine, fetch counts for each project
            project_counts = None
            if self.current_resource_type == ResourceType.CODE_ENGINE:
                project_counts = await self._fetch_code_engine_project_counts()
                # Store counts for use in project details modal
                self.project_counts = project_counts

            instance_table.update_instances(self.filtered_instances, project_counts)

            # Update statistics
            running = sum(1 for i in self.instances if i.status.value == "running")
            stopped = sum(1 for i in self.instances if i.status.value == "stopped")
            total = len(self.instances)

            status_bar.update_stats(
                total=total,
                running=running,
                stopped=stopped
            )

            # Update region selector with instance counts
            region_selector = self.query_one("#region_selector", RegionSelector)
            region_selector.update_instance_counts(total, running, stopped)

            status_bar.set_loading(False)

        except Exception as e:
            status_bar.set_loading(False)
            # Use call_from_thread to safely push screen from worker thread
            # Create ErrorScreen in main thread via lambda
            self.call_from_thread(
                lambda: self.push_screen(
                    ErrorScreen(
                        f"Failed to load instances: {e}",
                        recoverable=True,
                        suggestion="Press R to retry"
                    )
                )
            )

    async def _fetch_code_engine_project_counts(self) -> dict:
        """
        Fetch counts of apps, jobs, builds, and secrets for each Code Engine project
        
        Returns:
            Dict mapping project_id to counts: {project_id: {"apps": int, "jobs": int, "builds": int, "secrets": int}}
        """
        project_counts = {}
        
        if not self.instances:
            return project_counts
        
        try:
            # Fetch counts for all projects in parallel
            import asyncio
            tasks = []
            for instance in self.instances:
                tasks.append(self._fetch_single_project_counts(instance.id))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    ic(f"Error fetching counts for project {self.instances[i].id}: {result}")
                    project_counts[self.instances[i].id] = {"apps": 0, "jobs": 0, "builds": 0, "secrets": 0}
                else:
                    project_counts[self.instances[i].id] = result
                    
        except Exception as e:
            ic(f"Error fetching project counts: {e}")
        
        return project_counts

    async def _fetch_single_project_counts(self, project_id: str) -> dict:
        """Fetch counts for a single project"""
        try:
            apps, jobs, builds, secrets = await asyncio.gather(
                self.code_engine_client.list_apps(project_id),
                self.code_engine_client.list_jobs(project_id),
                self.code_engine_client.list_builds(project_id),
                self.code_engine_client.list_secrets(project_id),
                return_exceptions=True
            )
            
            apps_count = len(apps) if not isinstance(apps, Exception) else 0
            jobs_count = len(jobs) if not isinstance(jobs, Exception) else 0
            builds_count = len(builds) if not isinstance(builds, Exception) else 0
            secrets_count = len(secrets) if not isinstance(secrets, Exception) else 0
            
            return {
                "apps": apps_count,
                "jobs": jobs_count,
                "builds": builds_count,
                "secrets": secrets_count
            }
        except Exception as e:
            ic(f"Error fetching counts for project {project_id}: {e}")
            return {"apps": 0, "jobs": 0, "builds": 0, "secrets": 0}

    @work(thread=True, exclusive=True)
    async def load_project_resources(self, project_id: str) -> None:
        """Load apps, jobs, builds, and secrets for a Code Engine project"""
        try:
            status_bar = self.query_one("#status_bar", StatusBar)
            status_bar.set_loading(True)

            # Load all project resources in parallel
            apps, jobs, builds, secrets = await asyncio.gather(
                self.code_engine_client.list_apps(project_id),
                self.code_engine_client.list_jobs(project_id),
                self.code_engine_client.list_builds(project_id),
                self.code_engine_client.list_secrets(project_id),
                return_exceptions=True
            )

            # Handle exceptions
            if isinstance(apps, Exception):
                ic(f"Error loading apps: {apps}")
                apps = []
            if isinstance(jobs, Exception):
                ic(f"Error loading jobs: {jobs}")
                jobs = []
            if isinstance(builds, Exception):
                ic(f"Error loading builds: {builds}")
                builds = []
            if isinstance(secrets, Exception):
                ic(f"Error loading secrets: {secrets}")
                secrets = []

            self.project_apps = apps
            self.project_jobs = jobs
            self.project_builds = builds
            self.project_secrets = secrets

            # Update the instance table with project resources
            # Show apps by default
            self._update_project_resources_display()

            status_bar.set_loading(False)
            status_bar.set_message(
                f"Project: {len(apps)} apps, {len(jobs)} jobs, {len(builds)} builds, {len(secrets)} secrets (Press 1/2/3/4 to switch views)",
                "success"
            )

        except Exception as e:
            ic(f"Error loading project resources: {e}")
            status_bar = self.query_one("#status_bar", StatusBar)
            status_bar.set_loading(False)
            status_bar.set_message(f"Failed to load project resources: {str(e)[:50]}", "error")

    def _update_project_resources_display(self) -> None:
        """Update instance table to show Code Engine project resources"""
        instance_table = self.query_one("#instance_table", InstanceTable)
        
        # Convert Code Engine resources to Instance objects for display
        resources = []
        
        if self.project_resources_view == "apps":
            for app in self.project_apps:
                status_map = {
                    "ready": InstanceStatus.RUNNING,
                    "deploying": InstanceStatus.STARTING,
                    "failed": InstanceStatus.FAILED,
                    "stopped": InstanceStatus.STOPPED,
                }
                instance = Instance(
                    id=app.id,
                    name=app.name,
                    status=status_map.get(app.status, InstanceStatus.PENDING),
                    zone=self.current_region.name if self.current_region else "N/A",
                    vpc_name="Application",
                    vpc_id=app.project_id,
                    profile="App",
                    primary_ip=None,
                    created_at=app.created_at,
                    crn=""
                )
                resources.append(instance)
        elif self.project_resources_view == "jobs":
            for job in self.project_jobs:
                status_map = {
                    "ready": InstanceStatus.RUNNING,
                    "running": InstanceStatus.RUNNING,
                    "failed": InstanceStatus.FAILED,
                    "stopped": InstanceStatus.STOPPED,
                }
                instance = Instance(
                    id=job.id,
                    name=job.name,
                    status=status_map.get(job.status, InstanceStatus.PENDING),
                    zone=self.current_region.name if self.current_region else "N/A",
                    vpc_name="Job",
                    vpc_id=job.project_id,
                    profile="Job",
                    primary_ip=None,
                    created_at=job.created_at,
                    crn=""
                )
                resources.append(instance)
        elif self.project_resources_view == "builds":
            for build in self.project_builds:
                status_map = {
                    "ready": InstanceStatus.RUNNING,
                    "running": InstanceStatus.RUNNING,
                    "failed": InstanceStatus.FAILED,
                    "stopped": InstanceStatus.STOPPED,
                }
                instance = Instance(
                    id=build.id,
                    name=build.name,
                    status=status_map.get(build.status, InstanceStatus.PENDING),
                    zone=self.current_region.name if self.current_region else "N/A",
                    vpc_name="Build",
                    vpc_id=build.project_id,
                    profile="Build",
                    primary_ip=None,
                    created_at=build.created_at,
                    crn=""
                )
                resources.append(instance)
        elif self.project_resources_view == "secrets":
            for secret in self.project_secrets:
                # Secrets don't have status, so we'll show them all as RUNNING
                instance = Instance(
                    id=secret.id,
                    name=secret.name,
                    status=InstanceStatus.RUNNING,  # Secrets are always "active"
                    zone=self.current_region.name if self.current_region else "N/A",
                    vpc_name="Secret",
                    vpc_id=secret.project_id,
                    profile=secret.format,  # Show secret format as profile
                    primary_ip=None,
                    created_at=secret.created_at,
                    crn=""
                )
                resources.append(instance)

        self.instances = resources
        self.filtered_instances = resources
        instance_table.update_instances(resources, None)

    def apply_search_filter(self) -> None:
        """Filter instances based on search query"""
        if not self.search_query:
            self.filtered_instances = self.instances
            return

        query = self.search_query.lower()
        self.filtered_instances = [
            inst for inst in self.instances
            if query in inst.name.lower() or query in inst.status.value.lower()
        ]

    def on_region_selector_region_changed(self, message) -> None:
        """Handle region change event"""
        self.current_region = message.region
        
        # Update InfoBar with new region
        try:
            info_bar = self.query_one("#info_bar", InfoBar)
            info_bar.set_region(message.region)
        except:
            pass
        
        self.load_instances()

    def on_search_input_search_changed(self, message) -> None:
        """Handle search query change"""
        self.search_query = message.value
        self.apply_search_filter()

        instance_table = self.query_one("#instance_table", InstanceTable)
        instance_table.update_instances(self.filtered_instances, None)

    def on_search_input_search_cancelled(self) -> None:
        """Handle search cancellation"""
        self.search_query = ""
        self.apply_search_filter()

        instance_table = self.query_one("#instance_table", InstanceTable)
        instance_table.update_instances(self.filtered_instances, None)

    def on_resource_type_selector_resource_type_changed(self, message) -> None:
        """Handle resource type change event"""
        self.current_resource_type = message.resource_type

        # Switch to appropriate client
        client_map = {
            ResourceType.VPC: self.vpc_client,
            ResourceType.IKS: self.iks_client,
            ResourceType.ROKS: self.roks_client,
            ResourceType.CODE_ENGINE: self.code_engine_client,
        }
        self.client = client_map[message.resource_type]

        # Update resource type display in region selector
        resource_type_display_map = {
            ResourceType.VPC: "VPC Instances",
            ResourceType.IKS: "IKS Clusters",
            ResourceType.ROKS: "ROKS Clusters",
            ResourceType.CODE_ENGINE: "Code Engine Projects",
        }
        region_selector = self.query_one("#region_selector", RegionSelector)
        region_selector.set_resource_type_display(resource_type_display_map[message.resource_type])

        # Reset Code Engine project selection when switching away
        if message.resource_type != ResourceType.CODE_ENGINE:
            self.selected_project = None
            self.project_apps = []
            self.project_jobs = []
            self.project_builds = []
            self.project_secrets = []
            self.project_resources_view = "apps"
            self.project_counts = {}

        # Show notification
        status_bar = self.query_one("#status_bar", StatusBar)
        status_bar.set_message(f"Switched to {message.resource_type.value}", "info")

        # Reload regions for new resource type
        self.load_regions()

    def on_region_selector_resource_group_selection_requested(self, message) -> None:
        """Handle resource group selection request from region selector"""
        # If resource group is focused (keyboard navigation), directly change it
        if self.focused_section == "resource_group":
            region_selector = self.query_one("#region_selector", RegionSelector)
            new_rg = region_selector.selected_resource_group
            if new_rg and new_rg != self.current_resource_group:
                # Update app state
                self.current_resource_group = new_rg
                # Update Code Engine client
                self.code_engine_client.set_resource_group(new_rg.id)
                # Update InfoBar
                try:
                    info_bar = self.query_one("#info_bar", InfoBar)
                    info_bar.set_resource_group(new_rg)
                except:
                    pass
                # Show notification
                status_bar = self.query_one("#status_bar", StatusBar)
                status_bar.set_message(f"Resource Group: {new_rg.name}", "info")
                # Reload instances if viewing Code Engine
                if self.current_resource_type == ResourceType.CODE_ENGINE:
                    self.load_instances()
                    # Reset project selection
                    self.selected_project = None
                    self.project_apps = []
                    self.project_jobs = []
                    self.project_builds = []
                    self.project_secrets = []
                    self.project_counts = {}
        else:
            # Otherwise, open modal for selection
            self._open_resource_group_selector()

    def on_region_selector_theme_cycle_requested(self, message) -> None:
        """Handle theme cycle request from region selector - cycle theme"""
        self.action_cycle_theme()


    def _open_resource_group_selector(self) -> None:
        """Open resource group selection modal"""
        if not self.resource_groups:
            status_bar = self.query_one("#status_bar", StatusBar)
            status_bar.set_message("No resource groups available", "error")
            return

        # Open resource group selection modal
        def handle_selection(selected_rg: Optional[ResourceGroup]) -> None:
            if selected_rg:
                # Update region selector with new resource group (includes inline display)
                region_selector = self.query_one("#region_selector", RegionSelector)
                region_selector.set_resource_group(selected_rg)

                # Update app state
                self.current_resource_group = selected_rg

                # Update Code Engine client with new resource group
                self.code_engine_client.set_resource_group(selected_rg.id)

                # Update InfoBar with new resource group
                try:
                    info_bar = self.query_one("#info_bar", InfoBar)
                    info_bar.set_resource_group(selected_rg)
                except:
                    pass

                # Show notification
                status_bar = self.query_one("#status_bar", StatusBar)
                status_bar.set_message(f"Resource Group: {selected_rg.name}", "info")

                # Reload instances if viewing Code Engine
                if self.current_resource_type == ResourceType.CODE_ENGINE:
                    self.load_instances()
                    # Reset project selection when resource group changes
                    self.selected_project = None
                    self.project_apps = []
                    self.project_jobs = []
                    self.project_builds = []
                    self.project_secrets = []
                    self.project_counts = {}

        self.push_screen(
            ResourceGroupSelectionScreen(
                self.resource_groups,
                self.current_resource_group
            ),
            handle_selection
        )

    def action_region_next(self) -> None:
        """Select next region (l or → key) - context aware"""
        if self.focused_section == "resource_group":
            # Navigate resource groups
            region_selector = self.query_one("#region_selector", RegionSelector)
            region_selector.select_next_resource_group()
        elif self.focused_section == "region" or self.focused_section is None:
            # Navigate regions (default behavior)
            region_selector = self.query_one("#region_selector", RegionSelector)
            region_selector.select_next()
            # Auto-focus region section if not already focused
            if self.focused_section is None:
                self.focused_section = "region"
                region_selector.set_focused(True)

    def action_region_previous(self) -> None:
        """Select previous region (h or ← key) - context aware"""
        if self.focused_section == "resource_group":
            # Navigate resource groups
            region_selector = self.query_one("#region_selector", RegionSelector)
            region_selector.select_previous_resource_group()
        elif self.focused_section == "region" or self.focused_section is None:
            # Navigate regions (default behavior)
            region_selector = self.query_one("#region_selector", RegionSelector)
            region_selector.select_previous()
            # Auto-focus region section if not already focused
            if self.focused_section is None:
                self.focused_section = "region"
                region_selector.set_focused(True)

    def action_region_number(self, number: int) -> None:
        """Handle number key presses - context aware"""
        # If viewing Code Engine project resources, use 1-4 to switch views
        if self.current_resource_type == ResourceType.CODE_ENGINE and self.selected_project is not None:
            view_map = {1: "apps", 2: "jobs", 3: "builds", 4: "secrets"}
            if number in view_map:
                self.action_switch_ce_view(view_map[number])
                return
        
        # If regions are focused, use 0 and 5-9 for region selection
        if self.focused_section == "region":
            if number == 0 or (number >= 5 and number <= 9):
                region_selector = self.query_one("#region_selector", RegionSelector)
                region_selector.select_by_number(number)
                return
        
        # If 1-4 and regions not focused, these are handled by resource type switching
        # (The bindings will route 1-4 to switch_resource_type)
        # For 0 and 5-9 when not focused, select region
        if number == 0 or (number >= 5 and number <= 9):
            region_selector = self.query_one("#region_selector", RegionSelector)
            region_selector.select_by_number(number)
            # Auto-focus region section
            if self.focused_section != "region":
                self.focused_section = "region"
                region_selector.set_focused(True)

    def action_switch_resource_type(self, key: str) -> None:
        """Switch resource type by keyboard shortcut (1/2/3/4) - context aware"""
        # If viewing Code Engine project resources, use 1-4 for view switching instead
        if self.current_resource_type == ResourceType.CODE_ENGINE and self.selected_project is not None:
            view_map = {"1": "apps", "2": "jobs", "3": "builds", "4": "secrets"}
            if key in view_map:
                self.action_switch_ce_view(view_map[key])
                return
        
        # Otherwise, switch resource type
        resource_type_selector = self.query_one("#resource_type_selector", ResourceTypeSelector)
        resource_type_selector.select_by_key(key)
    
    def action_focus_region(self) -> None:
        """Focus region selector for keyboard navigation (r key)"""
        region_selector = self.query_one("#region_selector", RegionSelector)
        self.focused_section = "region"
        region_selector.set_focused(True)
        status_bar = self.query_one("#status_bar", StatusBar)
        status_bar.set_message("Region selector focused - use ←/→ to navigate, 0-9 to jump", "info")
    
    def action_focus_resource_group(self) -> None:
        """Focus resource group selector for keyboard navigation (g key)"""
        if not self.resource_groups:
            status_bar = self.query_one("#status_bar", StatusBar)
            status_bar.set_message("No resource groups available", "warning")
            return
        region_selector = self.query_one("#region_selector", RegionSelector)
        self.focused_section = "resource_group"
        region_selector.set_resource_group_focused(True)
        status_bar = self.query_one("#status_bar", StatusBar)
        status_bar.set_message("Resource group selector focused - use ←/→ to navigate", "info")
    
    def action_toggle_sidebar(self) -> None:
        """Toggle resource type selector sidebar visibility (Ctrl+b)"""
        resource_type_selector = self.query_one("#resource_type_selector", ResourceTypeSelector)
        resource_type_selector.toggle_visibility()
        status_bar = self.query_one("#status_bar", StatusBar)
        if resource_type_selector.visible:
            status_bar.set_message("Resource type selector shown", "info")
        else:
            status_bar.set_message("Resource type selector hidden", "info")

    def action_refresh(self) -> None:
        """Refresh current view"""
        self.load_instances()

    def action_cycle_theme(self) -> None:
        """Cycle through available color themes"""
        self.current_theme_index = (self.current_theme_index + 1) % len(self.THEMES)
        new_theme = self.THEMES[self.current_theme_index]
        self.theme = new_theme

        # Save theme preference
        self.preferences.update_theme(new_theme)

        # Update theme display in region selector
        try:
            region_selector = self.query_one("#region_selector", RegionSelector)
            region_selector.set_theme(new_theme)
        except:
            pass

        # Show notification of theme change
        status_bar = self.query_one("#status_bar", StatusBar)
        status_bar.set_message(f"Theme: {new_theme}", "info")

    def _start_auto_refresh(self) -> None:
        """Start auto-refresh timer"""
        if self._refresh_timer is not None:
            self._refresh_timer.stop()

        self._refresh_timer = self.set_interval(
            self.config.refresh_interval,
            self.load_instances,
            name="auto_refresh"
        )

    def _stop_auto_refresh(self) -> None:
        """Stop auto-refresh timer"""
        if self._refresh_timer is not None:
            self._refresh_timer.stop()
            self._refresh_timer = None

    def action_toggle_auto_refresh(self) -> None:
        """Toggle auto-refresh on/off"""
        new_state = self.preferences.toggle_auto_refresh()

        if new_state:
            self._start_auto_refresh()
            message = f"Auto-refresh enabled ({self.config.refresh_interval}s)"
        else:
            self._stop_auto_refresh()
            message = "Auto-refresh disabled"

        status_bar = self.query_one("#status_bar", StatusBar)
        status_bar.set_message(message, "info")

    def action_search(self) -> None:
        """Focus search input"""
        search_input = self.query_one("#search_input", SearchInput)
        search_input.focus_search()

    def action_show_details(self) -> None:
        """Show details for selected instance or Code Engine project in modal window"""
        instance_table = self.query_one("#instance_table", InstanceTable)
        selected = instance_table.get_selected_instance()

        if not selected:
            return

        # For Code Engine projects, show project details modal
        if self.current_resource_type == ResourceType.CODE_ENGINE and self.selected_project is None:
            # Viewing project list - show project details
            # Convert Instance back to CodeEngineProject for display
            # (The Instance represents a project when selected_project is None)

            # Get counts from cached project_counts
            counts = self.project_counts.get(selected.id, {
                "apps": 0, "jobs": 0, "builds": 0, "secrets": 0
            })

            project = CodeEngineProject(
                id=selected.id,
                name=selected.name,
                region=selected.zone,
                resource_group_id=selected.vpc_id,
                status="active",  # Assume active if showing in list
                created_at=selected.created_at,
                crn=selected.crn,
                entity_tag=None,
                apps_count=counts.get("apps", 0),
                jobs_count=counts.get("jobs", 0),
                builds_count=counts.get("builds", 0),
                secrets_count=counts.get("secrets", 0)
            )

            self.push_screen(CodeEngineProjectDetailScreen(project))
            return

        # For other resource types, show instance details modal
        self.push_screen(DetailScreen(selected))

        # Debug feedback
        status_bar = self.query_one("#status_bar", StatusBar)
        status_bar.set_message(f"Showing details for {selected.name}", "info")

    def action_select_project(self) -> None:
        """Select Code Engine project and load its resources (Enter key)"""
        instance_table = self.query_one("#instance_table", InstanceTable)
        selected = instance_table.get_selected_instance()

        if not selected:
            return

        # Only applicable for Code Engine projects
        if self.current_resource_type == ResourceType.CODE_ENGINE and self.selected_project is None:
            # Set selected project
            self.selected_project = selected

            # Load project resources directly (skip details modal)
            self.load_project_resources(selected.id)
            status_bar = self.query_one("#status_bar", StatusBar)
            status_bar.set_message(f"Loading resources for project '{selected.name}'...", "info")

    def on_code_engine_project_detail_screen_view_resources(
        self, message: CodeEngineProjectDetailScreen.ViewResources
    ) -> None:
        """Handle ViewResources message from project details modal"""
        # Find the project in instances list
        for instance in self.instances:
            if instance.id == message.project_id:
                self.selected_project = instance
                self.load_project_resources(message.project_id)
                status_bar = self.query_one("#status_bar", StatusBar)
                status_bar.set_message(f"Loading resources for project '{instance.name}'...", "info")
                break

    def action_back_to_projects(self) -> None:
        """Go back to Code Engine project list or unfocus sections (Esc key)"""
        # If a section is focused, unfocus it
        if self.focused_section:
            region_selector = self.query_one("#region_selector", RegionSelector)
            if self.focused_section == "region":
                region_selector.set_focused(False)
            elif self.focused_section == "resource_group":
                region_selector.set_resource_group_focused(False)
            self.focused_section = None
            status_bar = self.query_one("#status_bar", StatusBar)
            status_bar.set_message("Navigation unfocused", "info")
            return
        
        # Otherwise, go back from Code Engine project resources view to project list
        if self.current_resource_type != ResourceType.CODE_ENGINE or self.selected_project is None:
            return

        # Clear selected project and resources
        self.selected_project = None
        self.project_apps = []
        self.project_jobs = []
        self.project_builds = []
        self.project_secrets = []
        self.project_resources_view = "apps"

        # Reload project list
        self.load_instances()

        status_bar = self.query_one("#status_bar", StatusBar)
        status_bar.set_message("Returned to project list", "info")

    def action_switch_ce_view(self, view: str) -> None:
        """Switch Code Engine project resources view (apps/jobs/builds/secrets)"""
        # Only applicable when viewing Code Engine project resources
        if self.current_resource_type != ResourceType.CODE_ENGINE or self.selected_project is None:
            return

        # Validate view type
        if view not in ("apps", "jobs", "builds", "secrets"):
            return

        # Update view type
        self.project_resources_view = view

        # Update the display
        self._update_project_resources_display()

        # Update status bar with view type and counts
        counts = {
            "apps": len(self.project_apps),
            "jobs": len(self.project_jobs),
            "builds": len(self.project_builds),
            "secrets": len(self.project_secrets),
        }

        status_bar = self.query_one("#status_bar", StatusBar)
        status_bar.set_message(
            f"Viewing {view}: {counts[view]} items (Press 1:Apps 2:Jobs 3:Builds 4:Secrets)",
            "info"
        )

    def action_start_instance(self) -> None:
        """Start selected instance"""
        self._instance_action("start", "Start")

    def action_stop_instance(self) -> None:
        """Stop selected instance"""
        self._instance_action("stop", "Stop")

    def action_reboot_instance(self) -> None:
        """Reboot selected instance"""
        self._instance_action("reboot", "Reboot")

    def _instance_action(self, action: str, action_label: str) -> None:
        """Execute an action on the selected instance"""
        instance_table = self.query_one("#instance_table", InstanceTable)
        selected = instance_table.get_selected_instance()

        if not selected:
            return

        # Check if action is valid for instance state
        if action == "start" and not selected.can_start:
            self.push_screen(ErrorScreen(
                f"Cannot start instance in {selected.status.value} state",
                suggestion="Instance must be stopped to start"
            ))
            return
        elif action == "stop" and not selected.can_stop:
            self.push_screen(ErrorScreen(
                f"Cannot stop instance in {selected.status.value} state",
                suggestion="Instance must be running to stop"
            ))
            return
        elif action == "reboot" and not selected.can_reboot:
            self.push_screen(ErrorScreen(
                f"Cannot reboot instance in {selected.status.value} state",
                suggestion="Instance must be running to reboot"
            ))
            return

        # Show confirmation dialog
        def handle_confirm(confirmed: bool) -> None:
            if confirmed:
                self._execute_instance_action(selected.id, action, action_label)

        self.push_screen(
            ConfirmScreen(
                f"{action_label} instance '{selected.name}'?",
                f"This will {action} the instance {selected.short_id}"
            ),
            handle_confirm
        )

    @work(thread=True)
    async def _execute_instance_action(
        self,
        instance_id: str,
        action: str,
        action_label: str
    ) -> None:
        """Execute instance action via API"""
        try:
            status_bar = self.query_one("#status_bar", StatusBar)
            status_bar.set_message(f"Executing {action}...", "info")

            if action == "start":
                await self.client.start_instance(instance_id)
            elif action == "stop":
                await self.client.stop_instance(instance_id)
            elif action == "reboot":
                await self.client.reboot_instance(instance_id)

            status_bar.set_message(f"Instance {action} initiated successfully", "success")

            # Refresh after 2 seconds to show updated state
            self.set_timer(2.0, self.load_instances)

        except Exception as e:
            # Use call_from_thread to safely push screen from worker thread
            # Create ErrorScreen in main thread via lambda
            self.call_from_thread(
                lambda: self.push_screen(
                    ErrorScreen(
                        f"Failed to {action} instance: {e}",
                        recoverable=True,
                        suggestion="Check instance state and try again"
                    )
                )
            )

    def action_help(self) -> None:
        """Show help screen"""
        help_text = """
Blueterm - IBM Cloud Resource Manager

Keyboard Shortcuts:
  Resource Types:
    1              Switch to VPC
    2              Switch to IKS (IBM Kubernetes Service)
    3              Switch to ROKS (Red Hat OpenShift)
    4              Switch to Code Engine

  Top Navigation:
    r              Focus regions selector
    g              Focus resource group selector
    h/l or ←/→     Navigate within focused section
    0, 5-9         Jump to region by number (when regions focused)

  Main Navigation:
    j/k or ↑/↓     Navigate instances/resources
    h/l or ←/→     Switch regions (when not focused)
    0-9            Jump to region by number (when not focused)

  Actions:
    d              View instance/resource details (modal)
    s              Start selected instance
    S (Shift+S)    Stop selected instance
    b              Reboot selected instance
    R (Shift+R)    Refresh current view

  Code Engine:
    1-4            Switch view (Apps/Jobs/Builds/Secrets)
    Esc            Back to project list or unfocus section

  Detail Window:
    Esc, x, or q   Close detail window

  Search:
    /              Open search (filter by name/status)
    Esc            Close search

  Appearance:
    t              Cycle through color themes
    a              Toggle auto-refresh
    Ctrl+b         Toggle sidebar visibility

  General:
    ?              Show this help
    q              Quit application

Instance Status Colors:
  ● Green        Running
  ○ Red          Stopped
  ◐ Yellow       Starting/Stopping/Restarting
  ◎ Blue         Pending
  ✗ Red          Failed
"""
        self.push_screen(ErrorScreen(
            help_text,
            title="Help",
            recoverable=True
        ))
