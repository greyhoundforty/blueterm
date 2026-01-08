"""Entry point for blueterm application"""
import sys
from .app import BluetermApp
from .api.exceptions import ConfigurationError, AuthenticationError


def main():
    """
    Main entry point for blueterm.

    Launches the Textual TUI application for managing IBM Cloud VPC instances.
    """
    try:
        app = BluetermApp()
        app.run()
    except (ConfigurationError, AuthenticationError) as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        print("\nPlease ensure IBMCLOUD_API_KEY is set correctly.", file=sys.stderr)
        print("Get your API key from: https://cloud.ibm.com/iam/apikeys", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nExiting blueterm...")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
