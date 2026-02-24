# BlueTerm

## Overview
Python TUI for managing IBM Cloud resources (VPC instances, IKS/ROKS clusters, Code Engine apps). Inspired by TAWS. IBM Carbon dark theme by default.

## Tech Stack
- **Python 3.12**, **Textual** (TUI framework), **IBM Cloud SDKs** (`ibm-vpc`, `ibm-cloud-sdk-core`)
- **mise** for task running, **ruff** for lint/format, **mypy** for types
- Config stored in `~/.blueterm/config.toml` (theme, auto-refresh, last region)
- Auth via `IBMCLOUD_API_KEY` env var

## Project Structure
```
src/blueterm/
├── app.py                    # Main Textual app, keybindings, event handlers
├── config.py                 # Config, UserPreferences (TOML persistence)
├── api/
│   ├── client.py             # VPC API client (IAM token auto-refresh)
│   ├── iks_client.py         # IKS stub → Instance objects
│   ├── roks_client.py        # ROKS stub → Instance objects
│   ├── code_engine_client.py # Code Engine stub client
│   ├── resource_manager_client.py
│   └── models.py             # Region, Instance, InstanceStatus
├── widgets/
│   ├── top_navigation.py     # 3-column nav bar (resource type / region / group)
│   ├── instance_table.py
│   ├── status_bar.py
│   └── search_input.py
├── screens/
│   ├── detail_screen.py      # Instance detail modal (d key)
│   ├── confirm_screen.py
│   ├── error_screen.py
│   └── resource_group_selection_screen.py
└── styles/app.tcss           # IBM Carbon dark theme CSS
```

## Development Commands
```bash
mise run install    # pip install -e '.[dev]'
mise run run        # python -m blueterm
mise run test       # pytest with coverage
mise run lint       # ruff check
mise run format     # ruff format
mise run type-check # mypy
```

## Conventions
- **Keybindings**: capital letters for shift combos (`S` not `shift+s`)
- **Workers**: `@work` from `textual`, never `await` worker calls
- **TCSS**: no `:root` selector — use Python `Theme` objects via `register_theme()`
- **Resource switching**: all 4 clients initialized at startup; swap `self.client` on type change
- **Layout**: TopNavigation widget (3-column) → full-width InstanceTable → StatusBar
- **IBM Carbon palette**: bg `#161616`, surface `#262626`, primary `#0f62fe`, text `#f4f4f4`
- **IKS/ROKS display**: clusters converted to `Instance` objects in `list_instances()`
- **Stub data**: IKS/ROKS/Code Engine use stub data; real API integration is future work
