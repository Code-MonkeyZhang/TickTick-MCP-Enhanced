#!/usr/bin/env python3
# Use uv run test_server.py to run this script
"""
Simple test script to verify that the TickTick MCP server is configured correctly.
This will attempt to initialize the TickTick client and verify the credentials.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from ticktick_mcp.src.ticktick_client import TickTickClient
from ticktick_mcp.authenticate import main as auth_main

def test_ticktick_connection():
    """Test the connection to TickTick API."""
    print("Testing TickTick MCP server configuration...")
    
    # Load environment variables
    load_dotenv()
    
    # Check environment variables
    access_token = os.getenv("TICKTICK_ACCESS_TOKEN")
    client_id = os.getenv("TICKTICK_CLIENT_ID")
    client_secret = os.getenv("TICKTICK_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("❌ ERROR: TICKTICK_CLIENT_ID or TICKTICK_CLIENT_SECRET environment variables are not set.")
        print("Please register your application at https://developer.ticktick.com/manage")
        print("Then run 'uv run -m ticktick_mcp.cli auth' to set up your credentials.")
        return False
    
    if not access_token:
        print("❌ ERROR: TICKTICK_ACCESS_TOKEN environment variable is not set.")
        print("Would you like to authenticate with TickTick now? (y/n): ", end="")
        choice = input().lower().strip()
        if choice == 'y':
            # Run the auth flow
            auth_result = auth_main()
            if auth_result != 0:
                # Auth failed
                return False
            
            # Reload the environment after authentication
            load_dotenv()
        else:
            print("Please run 'uv run -m ticktick_mcp.cli auth' to authenticate with TickTick.")
            return False
    
    # Initialize TickTick client
    try:
        client = TickTickClient()
        print("✅ Successfully initialized TickTick client.")
        
        # Test API connectivity
        projects = client.get_all_projects()
        if 'error' in projects:
            print(f"❌ ERROR: Failed to fetch projects: {projects['error']}")
            print("Your access token may have expired. Try running 'uv run -m ticktick_mcp.cli auth' to refresh it.")
            return False
        
        print(f"✅ Successfully fetched {len(projects)} projects from TickTick.")
        for i, project in enumerate(projects, 1):
            print(f"  - {project.get('name', 'Unnamed project')} (ID: {project.get('id', 'No ID')})")
        
        # Test subtask creation if we have projects
        if projects:
            print("\n🧪 Testing subtask creation functionality...")
            test_project_id = projects[0].get('id')
            
            # Create a parent task
            parent_task = client.create_task(
                title="Test Parent Task",
                project_id=test_project_id,
                content="This is a test parent task"
            )
            
            if 'error' not in parent_task and 'id' in parent_task:
                parent_task_id = parent_task['id']
                print(f"✅ Created parent task: {parent_task.get('title')} (ID: {parent_task_id})")
                
                # Create a subtask
                subtask = client.create_subtask(
                    subtask_title="Test Subtask",
                    parent_task_id=parent_task_id,
                    project_id=test_project_id,
                    content="This is a test subtask"
                )
                
                if 'error' not in subtask:
                    print(f"✅ Created subtask: {subtask.get('title', 'Test Subtask')}")
                    
                    # Clean up test tasks
                    client.delete_task(test_project_id, parent_task_id)
                    if 'id' in subtask:
                        client.delete_task(test_project_id, subtask['id'])
                    print("🧹 Cleaned up test tasks")
                else:
                    print(f"❌ Failed to create subtask: {subtask.get('error', 'Unknown error')}")
                    # Clean up parent task
                    client.delete_task(test_project_id, parent_task_id)
            else:
                print(f"❌ Failed to create parent task: {parent_task.get('error', 'Unknown error')}")
            
        print("\nThe TickTick MCP server is configured correctly!")
        print("You can now run the server using 'uv run -m ticktick_mcp.cli run'")
        print("Or configure Claude for Desktop to use it.")
        return True
    
    except Exception as e:
        print(f"❌ ERROR: Failed to initialize TickTick client: {e}")
        return False

if __name__ == "__main__":
    result = test_ticktick_connection()
    sys.exit(0 if result else 1)