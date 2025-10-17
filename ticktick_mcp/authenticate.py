#!/usr/bin/env python3
"""
TickTick OAuth authentication command-line utility.

This script guides users through the process of authenticating with TickTick
and obtaining the necessary access tokens for the TickTick MCP server.
"""

import sys
import os
import logging
from typing import Optional
from pathlib import Path
from .src.auth import TickTickAuth, VERSION_CONFIGS

def main() -> int:
    """Run the authentication flow."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    print("""
╔════════════════════════════════════════════════╗
║       TickTick MCP Server Authentication       ║
╚════════════════════════════════════════════════╝
    
This utility will help you authenticate with TickTick
and obtain the necessary access tokens for the TickTick MCP server.
    """)
    
    # First, let user select the version
    selected_version = select_version()
    selected_config = VERSION_CONFIGS[selected_version]
    
    # Display version-specific information
    print(f"""
Before you begin, you will need:
1. A {selected_config['name']} account ({selected_config['account_url']})
2. A registered API application ({selected_config['developer_url']})
3. Your Client ID and Client Secret from the Developer Center
    """)
    
    # Check if .env file exists and already has credentials
    env_path = Path('.env')
    has_credentials = False
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            content = f.read()
            if 'TICKTICK_CLIENT_ID' in content and 'TICKTICK_CLIENT_SECRET' in content:
                has_credentials = True
    
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    
    if has_credentials:
        print("Existing credentials found in .env file.")
        use_existing = input("Do you want to use these credentials? (y/n): ").lower().strip()
        
        if use_existing == 'y':
            # Proceed with existing credentials (will be loaded by TickTickAuth)
            print("Using existing credentials from .env file.")
        else:
            # Ask for new credentials
            client_id = get_user_input("Enter your Client ID: ")
            client_secret = get_user_input("Enter your Client Secret: ")
    else:
        # No existing credentials, ask for new ones
        print("No existing credentials found in .env file.")
        client_id = get_user_input("Enter your Client ID: ")
        client_secret = get_user_input("Enter your Client Secret: ")
    
    # Initialize the auth manager
    auth = TickTickAuth(
        client_id=client_id,
        client_secret=client_secret
    )
    
    # Set the version configuration
    auth.set_version_config(selected_version)
    
    # Save version configuration to .env file
    auth.save_version_config_to_env(selected_version)
    
    print(f"\nStarting the OAuth authentication flow for {selected_config['name']}...")
    print("A browser window will open for you to authorize the application.")
    print("After authorization, you will be redirected back to this application.\n")
    
    # Start the OAuth flow
    result = auth.start_auth_flow()
    
    print("\n" + result)
    
    if "successful" in result.lower():
        print(f"""
Authentication complete! You can now use the {selected_config['name']} MCP server.

To start the server with Claude for Desktop:
1. Make sure you have configured Claude for Desktop
2. Restart Claude for Desktop
3. You should now see the TickTick tools available in Claude

Enjoy using {selected_config['name']} through Claude!
        """)
        return 0
    else:
        print("""
Authentication failed. Please try again or check the error message above.

Common issues:
- Incorrect Client ID or Client Secret
- Network connectivity problems
- Permission issues with the .env file

For further assistance, please refer to the documentation or raise an issue
on the GitHub repository.
        """)
        return 1

def select_version() -> str:
    """
    Ask user to select TickTick version and return the version key.
    
    Returns:
        Version key ('international' or 'china')
    """
    print("\nPlease select your account type:")
    print("1. TickTick International (ticktick.com)")
    print("2. TickTick China / 滴答清单 (dida365.com)")
    
    while True:
        choice = input("\nPlease enter your choice (1/2): ").strip()
        
        if choice == "1":
            config = VERSION_CONFIGS["international"]
            print(f"✓ You selected: {config['name']} ({config['account_url']})")
            return "international"
        elif choice == "2":
            config = VERSION_CONFIGS["china"]
            print(f"✓ You selected: {config['name']} ({config['account_url']})")
            return "china"
        else:
            print("Invalid choice, please enter 1 or 2")

def get_user_input(prompt: str) -> str:
    """Get user input with validation."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("This field cannot be empty. Please try again.")

if __name__ == "__main__":
    sys.exit(main())