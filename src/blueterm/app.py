"""Main Blueterm Application"""
from typing import Optional, List

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Header, Footer
from textual.worker import Worker, WorkerState

from .config import Config, UserPreferences
from .api.client import IBMCloudClient
from .api.models import Region, Instance
from .api.exceptions import AuthenticationError, ConfigurationError
from .widgets.region_selector import RegionSelector
from .widgets.instance_table import InstanceTable
from .widgets.status_bar import StatusBar
from .widgets.search_input import SearchInput
from .widgets.detail_panel import DetailPanel
from .screens.detail_screen import DetailScreen
from .screens.confirm_screen import ConfirmScreen
from .screens.error_screen import ErrorScreen


class BluetermApp(App):
    """
    Blueterm - IBM Cloud VPC Instance Manager TUI

    Keyboard Bindings:
        j/k or ↑/↓: Navigate instances
        h/l or ←/→: Switch regions
        /: Search/filter instances
        Enter: View instance details
        s: Start instance
        S: Stop instance
        r: Reboot instance
        R: Refresh current view
        q: Quit application
        ?: Show help
    """

    CSS_PATH = "styles/app.tcss"
    TITLE = "Blueterm - IBM Cloud VPC Manager"

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("question_mark", "help", "Help"),
        Binding("slash", "search", "Search"),
        Binding("r", "reboot_instance", "Reboot"),
        Binding("s", "start_instance", "Start"),
        Binding("S", "stop_instance", "Stop"),
        Binding("R", "refresh", "Refresh"),
        Binding("d", "show_details", "Details"),
        Binding("h", "region_previous", "Prev Region", show=False),
        Binding("l", "region_next", "Next Region", show=False),
        Binding("left", "region_previous", show=False),
        Binding("right", "region_next", show=False),
        # Number keys for quick region switching
        Binding("0", "region_number(0)", show=False),
        Binding("1", "region_number(1)", show=False),
        Binding("2", "region_number(2)", show=False),
        Binding("3", "region_number(3)", show=False),
        Binding("4", "region_number(4)", show=False),
        Binding("5", "region_number(5)", show=False),
        Binding("6", "region_number(6)", show=False),
        Binding("7", "region_number(7)", show=False),
        Binding("8", "region_number(8)", show=False),
        Binding("9", "region_number(9)", show=False),
        Binding("t", "cycle_theme", "Theme"),
        Binding("a", "toggle_auto_refresh", "Auto-refresh"),
    ]

    # Available color themes
    THEMES = [
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
        try:
            self.config = Config.from_env()
            self.config.validate()
            self.client = IBMCloudClient(self.config.api_key)
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
        self.instances: List[Instance] = []
        self.filtered_instances: List[Instance] = []
        self.search_query: str = ""
        self._refresh_timer = None  # Auto-refresh timer

    def compose(self) -> ComposeResult:
        """Compose the main application layout"""
        yield Header()
        yield Container(
            RegionSelector(id="region_selector"),
            InstanceTable(id="instance_table"),
            SearchInput(id="search_input"),
            id="main_container"
        )
        yield StatusBar(id="status_bar")
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize application on mount"""
        self.title = self.TITLE

        # Set theme from preferences
        self.theme = self.preferences.theme

        # Load regions
        self.load_regions()

        # Start auto-refresh if enabled
        if self.preferences.auto_refresh_enabled:
            self._start_auto_refresh()

    @work(thread=True, exclusive=True)
    async def load_regions(self) -> None:
        """Load available regions from API"""
        try:
            status_bar = self.query_one("#status_bar", StatusBar)
            status_bar.set_loading(True)

            self.regions = await self.client.list_regions()

            # Set default region
            default = next(
                (r for r in self.regions if r.name == self.config.default_region),
                self.regions[0] if self.regions else None
            )

            if default:
                self.current_region = default
                self.client.set_region(default.name)

                region_selector = self.query_one("#region_selector", RegionSelector)
                region_selector.set_regions(self.regions, default)

                self.load_instances()
            else:
                self.push_screen(ErrorScreen(
                    "No regions available",
                    recoverable=False,
                    suggestion="Check your IBM Cloud account configuration"
                ))

            status_bar.set_loading(False)

        except Exception as e:
            self.push_screen(ErrorScreen(
                f"Failed to load regions: {e}",
                recoverable=False,
                suggestion="Check your IBMCLOUD_API_KEY and network connectivity"
            ))

    @work(thread=True, exclusive=True)
    async def load_instances(self) -> None:
        """Load instances for current region"""
        if not self.current_region:
            return

        try:
            status_bar = self.query_one("#status_bar", StatusBar)
            status_bar.set_loading(True)

            self.instances = await self.client.list_instances(self.current_region.name)
            self.apply_search_filter()

            instance_table = self.query_one("#instance_table", InstanceTable)
            instance_table.update_instances(self.filtered_instances)

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
            self.push_screen(ErrorScreen(
                f"Failed to load instances: {e}",
                recoverable=True,
                suggestion="Press R to retry"
            ))

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
        self.load_instances()

    def on_search_input_search_changed(self, message) -> None:
        """Handle search query change"""
        self.search_query = message.value
        self.apply_search_filter()

        instance_table = self.query_one("#instance_table", InstanceTable)
        instance_table.update_instances(self.filtered_instances)

    def on_search_input_search_cancelled(self) -> None:
        """Handle search cancellation"""
        self.search_query = ""
        self.apply_search_filter()

        instance_table = self.query_one("#instance_table", InstanceTable)
        instance_table.update_instances(self.filtered_instances)

    def action_region_next(self) -> None:
        """Select next region (l or → key)"""
        region_selector = self.query_one("#region_selector", RegionSelector)
        region_selector.select_next()

    def action_region_previous(self) -> None:
        """Select previous region (h or ← key)"""
        region_selector = self.query_one("#region_selector", RegionSelector)
        region_selector.select_previous()

    def action_region_number(self, number: int) -> None:
        """Select region by number key (0-9)"""
        region_selector = self.query_one("#region_selector", RegionSelector)
        region_selector.select_by_number(number)

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
        """Show details for selected instance in modal window"""
        instance_table = self.query_one("#instance_table", InstanceTable)
        selected = instance_table.get_selected_instance()

        if selected:
            # Show modal detail screen
            self.push_screen(DetailScreen(selected))

            # Debug feedback
            status_bar = self.query_one("#status_bar", StatusBar)
            status_bar.set_message(f"Showing details for {selected.name}", "info")

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
            self.push_screen(ErrorScreen(
                f"Failed to {action} instance: {e}",
                recoverable=True,
                suggestion="Check instance state and try again"
            ))

    def action_help(self) -> None:
        """Show help screen"""
        help_text = """
Blueterm - IBM Cloud VPC Instance Manager

Keyboard Shortcuts:
  Navigation:
    j/k or ↑/↓     Navigate instances
    h/l or ←/→     Switch regions (cycle)
    0-9            Jump to region by number

  Actions:
    d              View instance details (modal)
    s              Start selected instance
    S (Shift+S)    Stop selected instance
    r              Reboot selected instance
    R (Shift+R)    Refresh instance list

  Detail Window:
    Esc, x, or q   Close detail window

  Search:
    /              Open search (filter by name/status)
    Esc            Close search

  Appearance:
    t              Cycle through color themes
    a              Toggle auto-refresh

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
