"""
Configuration management for TickTick MCP.

This module handles client initialization, environment variables,
and global configuration settings.
"""

import os
import logging
from dotenv import load_dotenv

from .ticktick_client import TickTickClient

# Set up logging
logger = logging.getLogger(__name__)

# Global client instance
ticktick = None


def initialize_client():
    """Initialize the TickTick client with proper authentication."""
    global ticktick
    try:
        # Check if .env file exists with access token
        load_dotenv()
        
        # Check if we have valid credentials
        if os.getenv("TICKTICK_ACCESS_TOKEN") is None:
            logger.error("No access token found in .env file. Please run 'uv run -m ticktick_mcp.cli auth' to authenticate.")
            return False
        
        # Initialize the client
        ticktick = TickTickClient()
        logger.info("TickTick client initialized successfully")
        
        # Test API connectivity
        projects = ticktick.get_all_projects()
        if 'error' in projects:
            logger.error(f"Failed to access TickTick API: {projects['error']}")
            logger.error("Your access token may have expired. Please run 'uv run -m ticktick_mcp.cli auth' to refresh it.")
            return False
            
        logger.info(f"Successfully connected to TickTick API with {len(projects)} projects")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize TickTick client: {e}")
        return False


def get_client():
    """Get the global TickTick client instance."""
    return ticktick


def ensure_client():
    """Ensure the client is initialized, initialize if not."""
    if not ticktick:
        if not initialize_client():
            raise RuntimeError("Failed to initialize TickTick client. Please check your API credentials.")
    return ticktick
