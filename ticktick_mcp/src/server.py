"""
Main MCP server for TickTick integration.

This is the core server that initializes the FastMCP server and registers
all the TickTick tools from the various modules.
"""

import logging
from mcp.server.fastmcp import FastMCP

from .config import initialize_client
from .tools import register_project_tools, register_task_tools, register_query_tools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP server
mcp = FastMCP("ticktick")


def register_all_tools():
    """Register all MCP tools from modules."""
    register_project_tools(mcp)
    register_task_tools(mcp)
    register_query_tools(mcp)
    logger.info("All TickTick MCP tools registered successfully")


def main():
    """Main entry point for the MCP server."""
    # Initialize the TickTick client
    if not initialize_client():
        logger.error("Failed to initialize TickTick client. Please check your API credentials.")
        return
    
    # Register all tools
    register_all_tools()
    
    # Run the server
    mcp.run(transport='stdio')


if __name__ == "__main__":
    main()
