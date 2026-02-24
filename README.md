# BlueTerm

Terminal UI for managing IBM Cloud resources.

BlueTerm is a keyboard-driven TUI for IBM Cloud VPC instances, Kubernetes clusters (IKS/ROKS), and Code Engine projects. Inspired by [TAWS](https://github.com/huseyinbabal/taws).

## Features

- **Multi-resource** — VPC, IKS, ROKS, and Code Engine in one interface
- **IBM Carbon design** — default dark theme with 9 theme options
- **Vim-style navigation** — j/k, h/l for power users
- **Resource actions** — start, stop, reboot with single keystrokes
- **Auto-refresh** — configurable interval, toggleable
- **Search/filter** — live filtering by name or status

## Prerequisites

- Python 3.9+
- IBM Cloud API key ([get one here](https://cloud.ibm.com/iam/apikeys))

## Installation

```bash
git clone https://github.com/yourusername/blueterm.git
cd blueterm
pip install -e '.[dev]'
# or: mise run install
```

## Configuration

```bash
export IBMCLOUD_API_KEY="your-api-key-here"

# Optional
export BLUETERM_DEFAULT_REGION="us-south"   # default: us-south
export BLUETERM_REFRESH_INTERVAL="30"       # seconds, default: 30
```

## Usage

```bash
python -m blueterm
# or: mise run dev
# or: blueterm (if installed via pip)
```

## Keyboard Shortcuts

### Navigation
| Key | Action |
|-----|--------|
| `1` `2` `3` `4` | Switch resource type (VPC / IKS / ROKS / Code Engine) |
| `r` | Focus region selector |
| `g` | Focus resource group selector |
| `h` `l` or `←` `→` | Navigate within focused section |
| `0` `5`-`9` | Jump to region by number |
| `j` `k` or `↑` `↓` | Move up/down in resource list |
| `Esc` | Unfocus nav / back to project list (Code Engine) |

### Resource Actions
| Key | Action |
|-----|--------|
| `d` | View details (modal) |
| `D` | Split-detail view |
| `Enter` | Load Code Engine project resources |
| `s` | Start instance |
| `S` | Stop instance |
| `b` | Reboot instance |
| `R` | Refresh |

### Other
| Key | Action |
|-----|--------|
| `/` | Search/filter |
| `t` | Cycle color themes |
| `a` | Toggle auto-refresh |
| `?` | Help |
| `q` | Quit |

### Code Engine views (when inside a project)
| Key | View |
|-----|------|
| `1` | Applications |
| `2` | Jobs |
| `3` | Builds |
| `4` | Secrets |

## Status Indicators

- `● Green` — Running
- `○ Red` — Stopped
- `◐ Yellow` — Starting / Stopping
- `◎ Blue` — Pending
- `✗ Red` — Failed

## License

MIT — see LICENSE file for details.

## Acknowledgments

- Inspired by [TAWS](https://github.com/huseyinbabal/taws) by Huseyin Babal
- Built with [Textual](https://textual.textualize.io/) by Will McGugan
