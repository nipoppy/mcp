"""
Nipoppy MCP Server

This server exposes a simple tool through the Model Context Protocol.
"""

from pathlib import Path
from typing import List

from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("Nipoppy Dataset Server", log_level="DEBUG")


@mcp.tool()
def list_installed_pipelines(nipoppy_root: Path) -> dict[str, dict[str, list[str]]]:
    """
    List installed Nipoppy pipelines.

    Args:
        nipoppy_root: Path to the Nipoppy dataset root.

    Returns:
        A dictionary mapping pipeline types to pipeline names and their versions.
    """

    from nipoppy.workflows.pipeline_store.list import PipelineListWorkflow

    workflow = PipelineListWorkflow(dpath_root=nipoppy_root)
    pipeline_info_map = {
        k.value: v for k, v in workflow._get_pipeline_info_map().items()
    }

    return pipeline_info_map


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
