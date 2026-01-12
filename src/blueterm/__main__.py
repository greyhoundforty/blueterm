"""Entry point for blueterm application"""
import sys
import os
from pathlib import Path
from icecream import ic, install

from .app import BluetermApp
from .api.exceptions import ConfigurationError, AuthenticationError


def setup_logging(debug: bool = False):
    """
    Configure icecream to log ONLY to files (not to console/TUI)
    
    Args:
        debug: If True, enable verbose debug logging
    """
    log_dir = Path.home() / ".blueterm"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "blueterm.log"
    debug_log_file = log_dir / "debug.log" if debug else None
    
    # File-only output function (no console output)
    def file_only_output(s):
        try:
            # Always write to main log file
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(s + "\n")
            
            # Also write to debug log if debug mode
            if debug and debug_log_file:
                with open(debug_log_file, "a", encoding="utf-8") as f:
                    f.write(s + "\n")
        except Exception as e:
            # Only print errors to stderr if we can't write logs
            print(f"Warning: Failed to write to log file: {e}", file=sys.stderr)
    
    # Configure with context for better debugging
    ic.configureOutput(
        outputFunction=file_only_output,
        includeContext=debug,  # Only include context in debug mode
        argToStringFunction=lambda x: str(x)[:200] if not debug else str(x)  # Truncate in non-debug
    )
    
    # Write initial log message (to file only)
    ic(f"Logging initialized. Log file: {log_file}, Debug: {debug}")
    if debug:
        ic(f"Debug log file: {debug_log_file}")
    
    return log_file


def main():
    """
    Main entry point for blueterm.

    Launches the Textual TUI application for managing IBM Cloud VPC instances.
    """
    # Check for debug mode
    debug_str = os.environ.get("BLUETERM_DEBUG", "false").lower()
    debug = debug_str in ("1", "true", "yes", "on")
    
    log_file = setup_logging(debug=debug)
    
    try:
        ic("Starting Blueterm application", f"Debug mode: {debug}")
        app = BluetermApp()
        app.run()
    except (ConfigurationError, AuthenticationError) as e:
        ic(f"Configuration Error: {e}")
        print(f"Configuration Error: {e}", file=sys.stderr)
        print("\nPlease ensure IBMCLOUD_API_KEY is set correctly.", file=sys.stderr)
        print("Get your API key from: https://cloud.ibm.com/iam/apikeys", file=sys.stderr)
        print(f"Check logs at: {log_file}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        ic("Application interrupted by user")
        print("\nExiting blueterm...")
        sys.exit(0)
    except Exception as e:
        ic(f"Unexpected error: {e}")
        print(f"Unexpected error: {e}", file=sys.stderr)
        print(f"Check logs at: {log_file}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
