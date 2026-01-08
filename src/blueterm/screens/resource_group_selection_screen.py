"""Resource group selection modal screen"""
from typing import List, Optional

from textual.app import ComposeResult
from textual.containers import Container, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static
from textual.widgets import OptionList
from textual.widgets.option_list import Option

from ..api.models import ResourceGroup


class ResourceGroupSelectionScreen(ModalScreen[Optional[ResourceGroup]]):
    """
    Modal screen for selecting a resource group from a list.

    Keyboard:
        Enter: Select highlighted resource group
        Esc or q: Cancel selection
        j/k or ↑/↓: Navigate list
    """

    DEFAULT_CSS = """
    ResourceGroupSelectionScreen {
        align: center middle;
    }

    ResourceGroupSelectionScreen > Container {
        width: 60;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: heavy $primary;
    }

    #rg_selection_header {
        height: auto;
        padding: 1 2;
        background: $primary;
        color: $text;
        text-style: bold;
    }

    #rg_selection_list {
        height: auto;
        max-height: 20;
        border: solid $accent;
        margin: 1 2;
    }

    #rg_selection_buttons {
        height: auto;
        padding: 1 2;
        align-horizontal: center;
    }

    #rg_selection_buttons Button {
        margin: 0 1;
    }
    """

    def __init__(self, resource_groups: List[ResourceGroup], current: Optional[ResourceGroup] = None, **kwargs):
        """
        Initialize resource group selection screen

        Args:
            resource_groups: List of available resource groups
            current: Currently selected resource group
        """
        super().__init__(**kwargs)
        self.resource_groups = resource_groups
        self.current_resource_group = current
        self.selected_resource_group: Optional[ResourceGroup] = None

    def compose(self) -> ComposeResult:
        """Compose resource group selection layout"""
        with Container(id="rg_selection_dialog"):
            with Vertical():
                # Header
                yield Label("Select Resource Group", id="rg_selection_header")

                # Resource group list
                option_list = OptionList(id="rg_selection_list")

                # Add resource groups as options
                for rg in self.resource_groups:
                    # Mark current selection
                    if self.current_resource_group and rg.id == self.current_resource_group.id:
                        option_list.add_option(Option(f"● {rg.name}", id=rg.id))
                    else:
                        option_list.add_option(Option(f"  {rg.name}", id=rg.id))

                yield option_list

                # Buttons
                with Container(id="rg_selection_buttons"):
                    yield Button("Select", variant="primary", id="select_button")
                    yield Button("Cancel", variant="default", id="cancel_button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "select_button":
            # Get selected option
            option_list = self.query_one(OptionList)
            if option_list.highlighted is not None:
                selected_id = option_list.get_option_at_index(option_list.highlighted).id
                # Find the resource group by ID
                selected_rg = next((rg for rg in self.resource_groups if rg.id == selected_id), None)
                self.dismiss(selected_rg)
            else:
                self.dismiss(None)
        else:
            # Cancel
            self.dismiss(None)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle option selection (Enter key or double-click)"""
        selected_id = event.option.id
        selected_rg = next((rg for rg in self.resource_groups if rg.id == selected_id), None)
        self.dismiss(selected_rg)

    def on_key(self, event) -> None:
        """Handle keyboard events"""
        if event.key in ("escape", "q"):
            self.dismiss(None)
