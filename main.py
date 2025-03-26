"""
Main entry point for the HubSpot MCP server
"""

# Import the mcp instance directly from the server.py file
from server import mcp

if __name__ == "__main__":
    mcp.run()
