"""
Nipoppy MCP Server

This server exposes a simple tool through the Model Context Protocol.
"""

import os
from pathlib import Path
from typing import List

from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("Nipoppy Dataset Server")


@mcp.tool()
def list_files(directory_path: str) -> List[str]:
    """
    List files in a directory.
    
    Args:
        directory_path: Path to the directory to list files from.
    
    Returns:
        List of file names in the directory.
    """
    path = Path(directory_path)
    
    if not path.exists():
        return [f"Error: Directory not found: {directory_path}"]
    
    if not path.is_dir():
        return [f"Error: Path is not a directory: {directory_path}"]
    
    try:
        files = [item.name for item in path.iterdir() if item.is_file()]
        return files
    except (PermissionError, OSError) as e:
        return [f"Error: Failed to list directory: {e}"]


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
