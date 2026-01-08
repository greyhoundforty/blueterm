"""Entry point for blueterm application"""
import sys
import os
from pathlib import Path
from icecream import ic, install

from .app import BluetermApp
from .api.exceptions import ConfigurationError, AuthenticationError


def setup_logging():
    """Configure icecream to log to a file"""
    log_dir = Path.home() / ".blueterm"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "blueterm.log"
    
    # Also output to stderr for immediate feedback and append to file
    def dual_output(s):
        print(s, file=sys.stderr)
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(s + "\n")
        except Exception as e:
            print(f"Warning: Failed to write to log file: {e}", file=sys.stderr)
    
    ic.configureOutput(outputFunction=dual_output, includeContext=True)
    
    ic(f"Logging initialized. Log file: {log_file}")
    return log_file


def main():
    """
    Main entry point for blueterm.

    Launches the Textual TUI application for managing IBM Cloud VPC instances.
    """
    log_file = setup_logging()
    
    try:
        ic("Starting Blueterm application")
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
