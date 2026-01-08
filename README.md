# BlueTerm

<p align="center">
  <b>Terminal UI for managing IBM Cloud VPC instances</b>
</p>

BlueTerm is a modern, keyboard-driven TUI (Terminal User Interface) application for managing IBM Cloud VPC virtual server instances. Inspired by [TAWS](https://github.com/huseyinbabal/taws) for AWS, BlueTerm brings the same powerful terminal-based workflow to IBM Cloud.

## Features

- 🚀 **Fast navigation** - Vim-style keybindings (j/k, h/l) for power users
- 🔢 **Quick region access** - Press 0-9 to jump instantly to any region
- 🌎 **Multi-region support** - Switch between IBM Cloud regions instantly
- 🔍 **Search and filter** - Quickly find instances by name or status
- ⚡ **Instance actions** - Start, stop, and reboot instances with single keystrokes
- 📊 **Real-time status** - Color-coded status indicators and live statistics in top bar
- 🔄 **Auto-refresh** - Configurable automatic refresh with toggle (press 'a')
- 🎨 **Theme persistence** - 9 beautiful color themes with saved preferences
- 💻 **TAWS-inspired UI** - Familiar layout for AWS TUI users
- ⌨️ **Keyboard-first** - Complete workflow without touching the mouse

## Prerequisites

- Python 3.9 or higher
- IBM Cloud account with VPC resources
- IBM Cloud API key

## Installation

### From source (Development)

```bash
# Clone the repository
git clone https://github.com/yourusername/blueterm.git
cd blueterm

# Install in development mode
mise run install
# or
pip install -e '.[dev]'
```

### From PyPI (Coming Soon)

```bash
pip install blueterm
```

## Configuration

BlueTerm requires an IBM Cloud API key to authenticate. Get your API key from:
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

# Enable debug mode
export BLUETERM_DEBUG="true"
```

### Using .env file

Create a `.env` file in your working directory:

```bash
cp .env.example .env
# Edit .env with your API key
```

### User Preferences

BlueTerm automatically saves your preferences to `~/.blueterm/config.toml`:

- **Theme**: Your selected color theme is remembered between sessions
- **Auto-refresh**: Your auto-refresh preference is saved
- **Last region**: The last selected region is remembered (future feature)

Preferences are saved automatically when changed. You can manually edit the config file or delete it to reset to defaults.

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

#### Navigation
- `j` or `↓` - Move down in instance list
- `k` or `↑` - Move up in instance list
- `h` or `←` - Previous region (cycle)
- `l` or `→` - Next region (cycle)
- `0-9` - Jump to region by number (quick access)

#### Instance Actions
- `d` - View instance details (pop-over modal)
- `s` - Start selected instance
- `S` (Shift+S) - Stop selected instance
- `r` - Reboot selected instance
- `R` (Shift+R) - Refresh instance list

#### Detail Window
- `Esc`, `x`, or `q` - Close detail window

#### Search
- `/` - Open search/filter
- `Esc` - Clear search and close
- Type to filter instances by name or status

#### Appearance
- `t` - Cycle through color themes
- `a` - Toggle auto-refresh on/off

#### General
- `?` - Show help screen
- `q` - Quit application

### Instance Status Indicators

- `● Green` - Running
- `○ Red` - Stopped
- `◐ Yellow` - Starting/Stopping/Restarting
- `◎ Blue` - Pending
- `✗ Red` - Failed

## Development

### Project Structure

```
blueterm/
├── src/blueterm/
│   ├── __init__.py
│   ├── __main__.py              # Entry point
│   ├── app.py                   # Main application
│   ├── config.py                # Configuration
│   ├── api/
│   │   ├── client.py            # IBM Cloud API client
│   │   ├── models.py            # Data models
│   │   └── exceptions.py        # Custom exceptions
│   ├── widgets/
│   │   ├── region_selector.py   # Region tabs
│   │   ├── instance_table.py    # Instance table
│   │   ├── status_bar.py        # Status bar
│   │   └── search_input.py      # Search input
│   ├── screens/
│   │   ├── detail_screen.py     # Instance details
│   │   ├── confirm_screen.py    # Confirmation dialog
│   │   └── error_screen.py      # Error display
│   └── styles/
│       └── app.tcss             # Textual CSS
├── tests/
├── pyproject.toml
└── mise.toml
```

### Development Commands

```bash
# Install dependencies
mise run install

# Run tests
mise run test

# Lint code
mise run lint

# Format code
mise run format

# Type checking
mise run type-check

# Clean build artifacts
mise run clean
```

### Running Tests

```bash
pytest
# or
mise run test
```

## Architecture

BlueTerm is built with:
- **Textual** - Modern TUI framework (5-10x faster than curses)
- **IBM VPC Python SDK** - Official IBM Cloud VPC client
- **Rich** - Beautiful terminal formatting
- **Python 3.9+** - Modern Python with type hints

### Key Components

1. **API Client** (`api/client.py`)
   - Wraps IBM VPC SDK
   - Automatic IAM token refresh (every 18 minutes)
   - Regional endpoint management
   - Error handling and retries

2. **Main App** (`app.py`)
   - Textual application with async workers
   - Keyboard binding handlers
   - Event-driven architecture

3. **Widgets**
   - **RegionSelector**: Horizontal region tabs
   - **InstanceTable**: Sortable data table
   - **SearchInput**: Live filtering
   - **StatusBar**: Statistics and messages

4. **Screens**
   - **DetailScreen**: Full instance information
   - **ConfirmScreen**: Action confirmation
   - **ErrorScreen**: Error display with recovery

## Roadmap

### MVP (Current)
- [x] VPC instance listing
- [x] Multi-region support
- [x] Instance actions (start/stop/reboot)
- [x] Search and filtering
- [x] Vim-style navigation
- [x] Instance details view

### Future Enhancements
- [ ] Code Engine support
- [ ] IKS/ROKS cluster management
- [ ] Command palette (`:` key)
- [ ] Multi-region view (grid layout)
- [ ] Configuration file support
- [ ] Auto-refresh with configurable interval
- [ ] Bulk actions (select multiple instances)
- [ ] Export instance data (JSON/CSV)
- [ ] Instance creation wizard
- [ ] VPC resource browser (subnets, security groups)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Troubleshooting

### "IBMCLOUD_API_KEY environment variable is required"
Make sure you've set the API key:
```bash
export IBMCLOUD_API_KEY="your-api-key"
```

### "Failed to authenticate with IBM Cloud"
- Verify your API key is correct
- Check your network connectivity
- Ensure your API key has VPC permissions

### "Failed to load regions"
- Check your IBM Cloud account has VPC enabled
- Verify API key has proper IAM permissions
- Check network connectivity to IBM Cloud

### Instance actions fail
- Verify instance state allows the action (e.g., can't stop a stopped instance)
- Check IAM permissions for instance actions
- Wait for pending operations to complete

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Inspired by [TAWS](https://github.com/huseyinbabal/taws) by Huseyin Babal
- Built with [Textual](https://textual.textualize.io/) by Will McGugan
- IBM Cloud VPC SDK by IBM

## Support

- 🐛 Issues: https://github.com/yourusername/blueterm/issues
- 📖 Documentation: https://github.com/yourusername/blueterm/wiki
- 💬 Discussions: https://github.com/yourusername/blueterm/discussions

---

**Made with ❤️ for IBM Cloud users who love their terminals**
