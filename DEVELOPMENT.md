# Development Guide

## Project Structure

```
blueterm/
├── src/blueterm/
│   ├── __init__.py
│   ├── __main__.py              # Entry point
│   ├── app.py                   # Main application
│   ├── config.py                # Configuration
│   ├── api/
│   │   ├── client.py            # VPC API client
│   │   ├── code_engine_client.py # Code Engine API client
│   │   ├── iks_client.py        # IKS API client
│   │   ├── roks_client.py       # ROKS API client
│   │   ├── resource_manager_client.py # Resource Manager API client
│   │   ├── models.py            # Data models
│   │   └── exceptions.py        # Custom exceptions
│   ├── widgets/
│   │   ├── region_selector.py   # Region selector
│   │   ├── resource_type_selector.py # Resource type sidebar
│   │   ├── instance_table.py    # Resource table
│   │   ├── status_bar.py        # Status bar
│   │   ├── info_bar.py          # Info bar
│   │   ├── search_input.py      # Search input
│   │   └── detail_panel.py      # Detail panel
│   ├── screens/
│   │   ├── detail_screen.py     # Resource details
│   │   ├── confirm_screen.py    # Confirmation dialog
│   │   ├── error_screen.py      # Error display
│   │   └── resource_group_selection_screen.py # Resource group selector
│   └── styles/
│       └── app.tcss             # Textual CSS
├── tests/
├── pyproject.toml
└── mise.toml
```

## Development Setup

### Prerequisites

- Python 3.9 or higher
- [mise](https://mise.jdx.dev/) (recommended) or pip/venv
- IBM Cloud API key

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/blueterm.git
cd blueterm

# Install dependencies
mise run install
# or
pip install -e '.[dev]'
```

### Development Commands

```bash
# Install dependencies
mise run install

# Run the application
mise run dev
# or
mise run run

# Run tests
mise run test
# or
pytest

# Lint code
mise run lint
# or
ruff check src/

# Format code
mise run format
# or
ruff format src/

# Type checking
mise run type-check
# or
mypy src/

# Clean build artifacts
mise run clean
```

## Architecture

### Key Components

1. **API Clients** (`api/`)
   - Wraps IBM Cloud SDKs
   - Automatic IAM token refresh
   - Regional endpoint management
   - Error handling and retries

2. **Main App** (`app.py`)
   - Textual application with async workers
   - Keyboard binding handlers
   - Event-driven architecture
   - Resource type switching

3. **Widgets** (`widgets/`)
   - **RegionSelector**: Region and resource group display
   - **ResourceTypeSelector**: Left sidebar for resource type selection
   - **InstanceTable**: Sortable data table with resource-specific columns
   - **SearchInput**: Live filtering
   - **StatusBar**: Statistics and messages
   - **InfoBar**: Region, resource group, and time display

4. **Screens** (`screens/`)
   - **DetailScreen**: Full resource information
   - **ConfirmScreen**: Action confirmation
   - **ErrorScreen**: Error display with recovery
   - **ResourceGroupSelectionScreen**: Resource group selection modal

### Async Workers

BlueTerm uses Textual's `@work` decorator for async operations:

- `load_regions()` - Fetches available regions
- `load_resource_groups()` - Fetches resource groups
- `load_instances()` - Fetches resources (instances, projects, etc.)
- `load_project_resources()` - Fetches Code Engine project resources

Workers run in separate threads and use `call_from_thread()` for UI updates.

### Resource Type System

The app supports multiple resource types:
- **VPC**: Virtual Private Cloud instances
- **IKS**: IBM Kubernetes Service clusters
- **ROKS**: Red Hat OpenShift clusters
- **Code Engine**: Projects with apps, jobs, builds, secrets

Each resource type has its own API client and can customize the table display.

## Adding New Resource Types

1. Create a new API client in `api/` (e.g., `new_service_client.py`)
2. Add the resource type to `ResourceType` enum in `widgets/resource_type_selector.py`
3. Add client initialization in `app.py.__init__()`
4. Add client mapping in `on_resource_type_selector_resource_type_changed()`
5. Update `InstanceTable` if custom columns are needed
6. Add region support (use VPC API to fetch all regions)

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/blueterm

# Run specific test file
pytest tests/test_client.py
```

## Code Style

- Follow PEP 8
- Use type hints
- Format with `ruff format`
- Lint with `ruff check`
- Type check with `mypy`

## Debugging

Enable debug logging:

```bash
export BLUETERM_DEBUG="true"
```

Logs are written to `~/.blueterm/blueterm.log` and stderr.

## Building

```bash
# Build package
python -m build

# Install from build
pip install dist/blueterm-*.whl
```
