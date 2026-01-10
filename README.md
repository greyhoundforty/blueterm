# BlueTerm

Terminal UI for managing IBM Cloud resources

BlueTerm is a keyboard-driven TUI (Terminal User Interface) application for managing IBM Cloud resources including VPC instances, Kubernetes clusters, OpenShift clusters, and Code Engine projects. Inspired by [TAWS](https://github.com/huseyinbabal/taws) for AWS, BlueTerm brings the same powerful terminal-based workflow to IBM Cloud.

## Features

- **Multi-resource support** - VPC instances, IKS clusters, ROKS clusters, and Code Engine projects in one interface
- **IBM Carbon Design** - Default IBM Carbon color scheme with multiple theme options
- **Fast navigation** - Vim-style keybindings (j/k, h/l) for power users
- **Quick region access** - Press 0-9 to jump instantly to any region
- **Multi-region support** - Switch between all IBM Cloud regions instantly
- **Search and filter** - Quickly find resources by name or status
- **Resource actions** - Start, stop, and reboot instances/clusters with single keystrokes
- **Real-time status** - Color-coded status indicators and live statistics
- **Auto-refresh** - Configurable automatic refresh with toggle
- **Theme support** - IBM Carbon, Nord, Gruvbox, Dracula, and 6 more themes
- **Code Engine integration** - View projects with app, job, build, and secret counts

## Prerequisites

- Python 3.9 or higher
- IBM Cloud account
- IBM Cloud API key

## Installation

### From source

```bash
git clone https://github.com/yourusername/blueterm.git
cd blueterm
mise run install
# or
pip install -e '.[dev]'
```

### From PyPI (Coming Soon)

```bash
pip install blueterm
```

## Configuration

BlueTerm requires an IBM Cloud API key. Get your API key from:
https://cloud.ibm.com/iam/apikeys

### Required Environment Variables

```bash
export IBMCLOUD_API_KEY="your-api-key-here"
```

### Optional Environment Variables

```bash
# Set default region (default: us-south)
export BLUETERM_DEFAULT_REGION="eu-gb"

# Set auto-refresh interval in seconds (default: 30)
export BLUETERM_REFRESH_INTERVAL="60"
```

### Using .env file

Create a `.env` file in your working directory:

```bash
cp .env.example .env
# Edit .env with your API key
```

## Usage

### Starting BlueTerm

```bash
# Run with mise
mise run dev

# Or run directly
python -m blueterm

# Or if installed via pip
blueterm
```

### Keyboard Shortcuts

#### Resource Types
- `v` - Switch to VPC (Virtual Private Cloud instances)
- `i` - Switch to IKS (IBM Kubernetes Service clusters)
- `r` - Switch to ROKS (Red Hat OpenShift clusters)
- `c` - Switch to Code Engine (projects with apps, jobs, builds, secrets)

#### Navigation
- `j` or `↓` - Move down in resource list
- `k` or `↑` - Move up in resource list
- `h` or `←` - Previous region (cycle)
- `l` or `→` - Next region (cycle)
- `0-9` - Jump to region by number (quick access)

#### Resource Actions
- `d` - View resource details (modal)
- `Enter` - Select Code Engine project (shows apps, jobs, builds)
- `s` - Start selected instance
- `S` (Shift+S) - Stop selected instance
- `b` - Reboot selected instance
- `R` (Shift+R) - Refresh current view

#### Search
- `/` - Open search/filter
- `Esc` - Clear search and close

#### Appearance
- `t` - Cycle through color themes (IBM Carbon, Nord, Gruvbox, Dracula, and more)
- `a` - Toggle auto-refresh on/off

#### General
- `?` - Show help screen
- `q` - Quit application

### Status Indicators

- `● Green` - Running
- `○ Red` - Stopped
- `◐ Yellow` - Starting/Stopping/Restarting
- `◎ Blue` - Pending
- `✗ Red` - Failed

## Code Engine

When viewing Code Engine projects, the table displays:
- **Name** - Project name
- **Apps** - Number of applications
- **Jobs** - Number of jobs
- **Builds** - Number of builds
- **Secrets** - Number of secrets

Press `Enter` or `d` on a project to view its resources (apps, jobs, builds).

## Documentation

- [Development Guide](DEVELOPMENT.md) - Setup, project structure, and development workflow
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions

## Architecture

BlueTerm is built with:
- **Textual** - Modern TUI framework
- **IBM Cloud Python SDKs** - Official IBM Cloud API clients
- **Rich** - Terminal formatting
- **Python 3.9+** - Modern Python with type hints

## Contributing

Contributions are welcome! Please see [DEVELOPMENT.md](DEVELOPMENT.md) for setup instructions.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Inspired by [TAWS](https://github.com/huseyinbabal/taws) by Huseyin Babal
- Built with [Textual](https://textual.textualize.io/) by Will McGugan
- IBM Cloud SDKs by IBM
